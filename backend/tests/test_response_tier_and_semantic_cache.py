import pytest
import time
from app.reasoning.core import ReasoningPlatform, ReasoningCache
from app.reasoning.chief import ReasoningResult, RiskAssessment
from app.reasoning.response_tier import (
    ResponseTier,
    TierMetricsTracker,
    classify_query_tier,
    format_tier1_templated_response,
    generate_tier2_cheap_llm_response,
    generate_tier3_full_llm_response,
    process_response_tier,
    tier_tracker,
)
from app.schemas.evidence import BaseEvidence
from app.core.container import Container
from app.orchestrator.orchestrator import AgentOrchestrator
from app.schemas.requests import ExecutionRequest


def test_classify_query_tier():
    # 1. High confidence simple lookup -> Tier 1
    ev_high = BaseEvidence(id="ev-1", source="Market", agent="MarketAgent", confidence=0.9, weight=1.0, reasoning="Wheat price is 2275 INR")
    tier1 = classify_query_tier("what is the price of wheat in Punjab today", 0.90, [ev_high])
    assert tier1 == ResponseTier.TIER_1_RETRIEVAL_ONLY

    # 2. Moderate confidence simple lookup -> Tier 2
    ev_mod = BaseEvidence(id="ev-2", source="Knowledge", agent="KnowledgeAgent", confidence=0.6, weight=1.0, reasoning="Apply fertilizer split")
    tier2 = classify_query_tier("wheat fertilizer dose", 0.60, [ev_mod])
    assert tier2 == ResponseTier.TIER_2_CHEAP_LLM

    # 3. Low confidence -> Tier 3
    ev_low = BaseEvidence(id="ev-3", source="Unknown", agent="Unknown", confidence=0.3, weight=1.0, reasoning="Unsure")
    tier3_low = classify_query_tier("rare crop anomaly", 0.30, [ev_low])
    assert tier3_low == ResponseTier.TIER_3_FULL_LLM

    # 4. Multi-factor complex query (weather + crop stage + disease risk) -> Tier 3 regardless of confidence
    tier3_multi = classify_query_tier(
        "It is raining in Ludhiana and my wheat crop has yellow spots, what spray is recommended along with fertilizer?",
        0.85,
        [ev_high]
    )
    assert tier3_multi == ResponseTier.TIER_3_FULL_LLM


def test_tier1_templated_response_formatting():
    # Market Price query
    res_market = format_tier1_templated_response(
        query="what is the price of wheat in Punjab today",
        top_reasoning="[HIGH CONFIDENCE] Based on Market evidence for Wheat in Punjab: Wheat mandi price in Ludhiana is 2275 INR/quintal.",
        crop="Wheat",
        location="Ludhiana, Punjab",
        metadata={"price": "2,275 INR per quintal"}
    )
    assert "2,275 INR" in res_market
    assert "[HIGH CONFIDENCE]" not in res_market
    assert "Wheat" in res_market

    # Scheme Eligibility query
    res_scheme = format_tier1_templated_response(
        query="am I eligible for PM Kisan scheme",
        top_reasoning="The PM-KISAN scheme provides income support of INR 6,000 per year...",
        crop="Wheat",
        location="Punjab"
    )
    assert "PM-Kisan" in res_scheme
    assert "6,000 rupees" in res_scheme

    # Weather query
    res_weather = format_tier1_templated_response(
        query="what is the weather in Ludhiana",
        top_reasoning="Temperature reads 28C clear sky",
        crop="Wheat",
        location="Ludhiana"
    )
    assert "weather forecast indicates" in res_weather


def test_semantic_similarity_cache():
    cache = ReasoningCache(similarity_threshold=0.80)

    q1 = "what is the price of wheat in Punjab today"
    res1 = ReasoningResult(
        result_id="RES-101",
        session_id="SES-101",
        trace_id="TRC-101",
        query=q1,
        primary_recommendation="The current mandi price for Wheat in Ludhiana, Punjab is 2,275 INR per quintal.",
        summary="Wheat mandi price advisory",
        suggested_actions=["Check local mandi"],
        risk_assessment=RiskAssessment(risk_score=0.1, risk_level="low"),
        overall_confidence=0.9,
        explanation="High confidence market data."
    )

    # Set cache with query 1
    cache.set(q1, res1, language="en")

    # 1. Exact lookup
    cached_exact = cache.get(q1, language="en")
    assert cached_exact is not None
    assert cached_exact.result_id == "RES-101"

    # 2. Semantic reworded lookup ("wheat mandi price in Punjab")
    q2 = "wheat mandi price in Punjab"
    cached_semantic = cache.get(q2, language="en")
    assert cached_semantic is not None, "Reworded query should hit semantic cache!"
    assert cached_semantic.result_id == "RES-101"
    assert cache.stats["hits"] >= 2


@pytest.mark.asyncio
async def test_self_test_loop_10_queries():
    """
    Self-Test Loop:
    1. Runs 5 original queries + 5 reworded near-duplicates.
    2. Verifies reworded queries hit semantic cache / Tier 1.
    3. Verifies simple queries land in Tier 1 and complex multi-factor reach Tier 3.
    4. Computes tier distribution % and cost savings.
    """
    tier_tracker.reset()
    container = Container()
    orchestrator = AgentOrchestrator(container)

    # 5 Original Queries
    original_queries = [
        "what is the price of wheat in Ludhiana today",                             # Simple lookup -> Tier 1
        "am I eligible for PM Kisan scheme",                                       # Simple lookup -> Tier 1
        "what is the agronomic guide for wheat sowing depth",                       # Simple lookup -> Tier 1
        "what fertilizer dose should I use for wheat",                              # Moderate -> Tier 2
        "It is raining in Ludhiana and my wheat has yellow spots, what spray is recommended along with fertilizer?" # Multi-factor -> Tier 3
    ]

    # 5 Reworded Near-Duplicate Queries
    reworded_queries = [
        "what's the mandi rate for wheat in Ludhiana",                             # Duplicate of Q1 -> Semantic Cache / Tier 1
        "how much money do farmers get under PM-Kisan scheme",                     # Duplicate of Q2 -> Semantic Cache / Tier 1
        "at what depth should I sow wheat seeds",                                  # Duplicate of Q3 -> Semantic Cache / Tier 1
        "how much fertilizer split for wheat crop",                                # Duplicate of Q4 -> Semantic Cache / Tier 2
        "Heavy rain and yellow rust spots on wheat crop, what chemical to spray and when to apply fertilizer?" # Duplicate of Q5 -> Tier 3
    ]

    all_queries = original_queries + reworded_queries
    responses = []

    for q in all_queries:
        req = ExecutionRequest(session_id="test-session", query=q, farmer_id="farmer_ramesh")
        res = await orchestrator.execute_query(req)
        assert res.status == "success"
        responses.append(res)

    summary = tier_tracker.get_summary()

    # Confirmations
    assert summary["total_queries"] == 10
    t1_count = summary["tier_counts"]["Tier 1"]
    t2_count = summary["tier_counts"]["Tier 2"]
    t3_count = summary["tier_counts"]["Tier 3"]

    assert t1_count >= 5, f"Expected at least 5 Tier 1 queries, got {t1_count}"
    assert t3_count >= 2, f"Expected at least 2 Tier 3 queries, got {t3_count}"

    print("\n" + "="*60)
    print("SELF-TEST TIER DISTRIBUTION SUMMARY:")
    print("Headline:", summary["headline_summary"])
    print("Distribution:", summary["tier_distribution"])
    print("Total Cost USD:", summary["estimated_total_cost_usd"])
    print("Baseline Full LLM Cost USD:", summary["baseline_full_llm_cost_usd"])
    print("Cost Savings %:", summary["cost_savings_percent"])
    print("="*60 + "\n")
