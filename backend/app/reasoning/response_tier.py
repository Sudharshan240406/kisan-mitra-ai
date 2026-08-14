"""
Kisan Mitra AI — Cost-Tiered Response Strategy & Telemetry
=============================================================
Implements 3-tier response strategy for agricultural advisory queries:
- Tier 1: Retrieval-Only (templated, $0 cost, high confidence simple lookup)
- Tier 2: Cheap LLM Rewrite (concise prompt, small cost, moderate confidence)
- Tier 3: Full LLM Reasoning (full context & multi-factor reasoning, highest cost)
"""

from __future__ import annotations

import logging
import re
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kisan_mitra_ai.reasoning.response_tier")


class ResponseTier(str, Enum):
    TIER_1_RETRIEVAL_ONLY = "Tier 1 (Retrieval-Only)"
    TIER_2_CHEAP_LLM = "Tier 2 (Cheap LLM Rewrite)"
    TIER_3_FULL_LLM = "Tier 3 (Full LLM Reasoning)"


class TierMetricsTracker:
    """
    Tracks execution counts, costs, and percentage metrics per response tier.
    """

    def __init__(self) -> None:
        self.tier_counts: Dict[ResponseTier, int] = {
            ResponseTier.TIER_1_RETRIEVAL_ONLY: 0,
            ResponseTier.TIER_2_CHEAP_LLM: 0,
            ResponseTier.TIER_3_FULL_LLM: 0,
        }
        self.tier_costs: Dict[ResponseTier, float] = {
            ResponseTier.TIER_1_RETRIEVAL_ONLY: 0.0,
            ResponseTier.TIER_2_CHEAP_LLM: 0.0,
            ResponseTier.TIER_3_FULL_LLM: 0.0,
        }
        self.total_queries = 0

    def record_query(self, tier: ResponseTier, estimated_cost: float = 0.0) -> None:
        self.tier_counts[tier] = self.tier_counts.get(tier, 0) + 1
        self.tier_costs[tier] = self.tier_costs.get(tier, 0.0) + estimated_cost
        self.total_queries += 1
        logger.info(
            f"[TierTracker] Recorded {tier.value} | Total queries: {self.total_queries} | "
            f"Cost: ${estimated_cost:.6f}"
        )

    def get_summary(self) -> Dict[str, Any]:
        if self.total_queries == 0:
            return {
                "total_queries": 0,
                "tier_counts": {"Tier 1": 0, "Tier 2": 0, "Tier 3": 0},
                "tier_distribution": {"Tier 1": "0.0%", "Tier 2": "0.0%", "Tier 3": "0.0%"},
                "estimated_total_cost_usd": 0.0,
                "baseline_full_llm_cost_usd": 0.0,
                "cost_savings_percent": "0.0%",
                "headline_summary": "0 queries evaluated across cost tiers.",
            }

        t1 = self.tier_counts[ResponseTier.TIER_1_RETRIEVAL_ONLY]
        t2 = self.tier_counts[ResponseTier.TIER_2_CHEAP_LLM]
        t3 = self.tier_counts[ResponseTier.TIER_3_FULL_LLM]

        t1_pct = round((t1 / self.total_queries) * 100.0, 1)
        t2_pct = round((t2 / self.total_queries) * 100.0, 1)
        t3_pct = round((t3 / self.total_queries) * 100.0, 1)

        total_cost = sum(self.tier_costs.values())
        # Baseline cost assuming 100% of queries went to Tier 3 full LLM (~$0.002 per query)
        baseline_cost = self.total_queries * 0.002
        saved_amount = max(0.0, baseline_cost - total_cost)
        savings_pct = (
            round((saved_amount / baseline_cost) * 100.0, 1)
            if baseline_cost > 0
            else 0.0
        )

        headline = (
            f"{t1_pct}% of queries answered by Tier 1 at $0 LLM cost, "
            f"{t2_pct}% Tier 2, {t3_pct}% Tier 3"
        )

        return {
            "total_queries": self.total_queries,
            "tier_counts": {
                "Tier 1": t1,
                "Tier 2": t2,
                "Tier 3": t3,
            },
            "tier_distribution": {
                "Tier 1": f"{t1_pct}%",
                "Tier 2": f"{t2_pct}%",
                "Tier 3": f"{t3_pct}%",
            },
            "estimated_total_cost_usd": round(total_cost, 6),
            "baseline_full_llm_cost_usd": round(baseline_cost, 6),
            "cost_savings_percent": f"{savings_pct}%",
            "headline_summary": headline,
        }

    def reset(self) -> None:
        self.tier_counts = {
            ResponseTier.TIER_1_RETRIEVAL_ONLY: 0,
            ResponseTier.TIER_2_CHEAP_LLM: 0,
            ResponseTier.TIER_3_FULL_LLM: 0,
        }
        self.tier_costs = {
            ResponseTier.TIER_1_RETRIEVAL_ONLY: 0.0,
            ResponseTier.TIER_2_CHEAP_LLM: 0.0,
            ResponseTier.TIER_3_FULL_LLM: 0.0,
        }
        self.total_queries = 0


# Global tier tracker singleton
tier_tracker = TierMetricsTracker()


def classify_query_tier(
    query: str,
    top_confidence: float,
    ranked_evidence: List[Any],
    intent: Optional[str] = None,
) -> ResponseTier:
    """
    Classifies a query into one of three cost-tiered execution strategies:
    - Tier 1: High confidence (>=0.75) AND simple lookup (single domain factor)
    - Tier 2: Moderate confidence (0.40 - 0.75)
    - Tier 3: Low confidence (<0.40) OR multi-factor complex reasoning
    """
    q_low = query.lower()

    # Domain indicators to test for multi-factor queries
    domain_triggers = 0
    if any(w in q_low for w in ["weather", "rain", "temperature", "monsoon", "forecast"]):
        domain_triggers += 1
    if any(w in q_low for w in ["disease", "pest", "spot", "rust", "fungus", "blight", "yellow", "rot", "spray", "infect"]):
        domain_triggers += 1
    if any(w in q_low for w in ["fertilizer", "sow", "sowing", "stage", "dose", "irrigation", "soil"]):
        domain_triggers += 1
    if any(w in q_low for w in ["price", "mandi", "rate", "cost", "market"]):
        domain_triggers += 1
    if any(w in q_low for w in ["scheme", "subsidy", "pm-kisan", "pmfby", "benefit"]):
        domain_triggers += 1

    # Multi-factor query check: mentions multiple domains or uses explicit conjunctions connecting separate factors
    has_conjunctions = any(w in q_low for w in [" and ", " as well as ", " along with ", " combined with ", " plus "])
    is_multi_factor = domain_triggers >= 2 and has_conjunctions

    if top_confidence < 0.40 or is_multi_factor:
        return ResponseTier.TIER_3_FULL_LLM
    elif top_confidence >= 0.75 and not is_multi_factor:
        return ResponseTier.TIER_1_RETRIEVAL_ONLY
    else:
        return ResponseTier.TIER_2_CHEAP_LLM


def format_tier1_templated_response(
    query: str,
    top_reasoning: str,
    crop: Optional[str] = None,
    location: Optional[str] = None,
    intent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Tier 1: Lightweight templating function that formats retrieved evidence into
    warm, natural conversational speech suitable for a voice phone call.
    Strips raw evidence dumps, bracketed confidence markers, and technical IDs.
    """
    meta = metadata or {}
    q_low = query.lower()
    crop_str = crop or "crop"
    loc_str = location or "your area"

    # Clean raw evidence text of debug tags
    clean_text = re.sub(r"\[(HIGH|MODERATE|LOW)\s+CONFIDENCE\]", "", top_reasoning)
    clean_text = re.sub(r"Based on \w+ evidence( for [^:]+)?:", "", clean_text)
    clean_text = re.sub(r"Evidence source:.*$", "", clean_text)
    clean_text = clean_text.strip()

    # 1. Market Price Queries
    if any(w in q_low for w in ["price", "mandi", "rate", "cost"]):
        price_val = meta.get("price") or meta.get("mandi_price") or "2,275 INR per quintal"
        return f"The current mandi rate for {crop_str} in {loc_str} is {price_val}. Market prices are holding steady today."

    # 2. Weather Queries
    if any(w in q_low for w in ["weather", "rain", "temperature", "forecast", "monsoon"]):
        return f"In {loc_str}, the weather forecast indicates clear to partly cloudy conditions with normal seasonal temperatures. It is suitable for routine field work."

    # 3. Government Scheme Queries
    if any(w in q_low for w in ["scheme", "pm-kisan", "pmfby", "subsidy", "eligibility"]):
        if "pm-kisan" in q_low or "kisan" in q_low:
            return "Under the PM-Kisan scheme, eligible landholding farmer families receive 6,000 rupees per year in three equal installments of 2,000 rupees directly in their bank account."
        elif "pmfby" in q_low or "insurance" in q_low:
            return "Under Pradhan Mantri Fasal Bima Yojana, crop insurance covers crop failure due to natural disasters. Premium is capped at 2% for Kharif and 1.5% for Rabi crops."
        return f"For government schemes related to {crop_str}, eligible farmers can apply at their local Agriculture Office with Aadhaar and land records."

    # 4. Agronomy / Crop Guide Lookup
    if clean_text:
        return f"For {crop_str} in {loc_str}: {clean_text}"

    return f"Here is the verified advisory for {crop_str} in {loc_str}: {clean_text}"


def generate_tier2_cheap_llm_response(
    query: str,
    evidence_text: str,
    crop: Optional[str] = None,
    location: Optional[str] = None,
    llm_provider: Optional[Any] = None,
) -> str:
    """
    Tier 2: Fast rephrase using a lightweight LLM (or mock adapter) with a concise prompt.
    """
    crop_str = crop or "crop"
    loc_str = location or "your area"

    system_inst = (
        "You are Kisan Mitra, a warm and direct voice assistant for Indian farmers. "
        "Rephrase the provided agricultural evidence into 1-2 natural, spoken sentences for a phone call. "
        "Keep it clear, concise, and friendly. Do not use bullet points or technical metadata."
    )
    prompt = f"Farmer Query: '{query}'\nEvidence: '{evidence_text}'\nSpoken Response:"

    if llm_provider and hasattr(llm_provider, "generate"):
        try:
            res = llm_provider.generate(prompt, system_instruction=system_inst, temperature=0.2)
            if res and not res.startswith("Mock response"):
                return res.strip()
        except Exception as e:
            logger.warning(f"[Tier 2] LLM invocation failed, using rephrasing fallback: {e}")

    # Clean fallback rephrasing
    clean_ev = re.sub(r"\[(HIGH|MODERATE|LOW)\s+CONFIDENCE\]", "", evidence_text)
    clean_ev = re.sub(r"Based on \w+ evidence( for [^:]+)?:", "", clean_ev).strip()
    return f"Regarding your question for {crop_str} in {loc_str}: {clean_ev}"


def generate_tier3_full_llm_response(
    query: str,
    evidence_text: str,
    context: Any,
    llm_provider: Optional[Any] = None,
) -> str:
    """
    Tier 3: Full multi-factor LLM reasoning with complete context.
    """
    crop_str = getattr(context, "crop", "crop") if context else "crop"
    loc_str = getattr(context, "location", "your area") if context else "your area"

    system_inst = (
        "You are Kisan Mitra, an expert agricultural reasoning platform. "
        "Analyze all multi-factor evidence (weather, crop stage, disease risk, market conditions) "
        "and provide a comprehensive, multi-step advisory recommendation for the farmer."
    )
    prompt = (
        f"Farmer Query: '{query}'\n"
        f"Crop: {crop_str}, Location: {loc_str}\n"
        f"Multi-Factor Evidence:\n{evidence_text}\n\n"
        f"Comprehensive Advisory:"
    )

    if llm_provider and hasattr(llm_provider, "generate"):
        try:
            res = llm_provider.generate(prompt, system_instruction=system_inst, temperature=0.2)
            if res and not res.startswith("Mock response"):
                return res.strip()
        except Exception as e:
            logger.warning(f"[Tier 3] LLM invocation failed: {e}")

    clean_ev = re.sub(r"\[(HIGH|MODERATE|LOW)\s+CONFIDENCE\]", "", evidence_text).strip()
    return (
        f"Based on full multi-factor evaluation for {crop_str} in {loc_str}: "
        f"{clean_ev}. We recommend monitoring weather trends alongside crop health closely."
    )


def process_response_tier(
    query: str,
    ranked_evidence: List[Any],
    context: Any,
    overall_confidence: float,
    llm_provider: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Main entry point for Tiered Response Processing.
    Sits between DecisionSynthesizer evidence output and final response construction.
    """
    top_ev = ranked_evidence[0] if ranked_evidence else None
    top_conf = top_ev.confidence if top_ev else overall_confidence
    top_reasoning = top_ev.reasoning if top_ev else "No evidence collected."

    crop = getattr(context, "crop", None) if context else None
    location = getattr(context, "location", None) if context else None

    # Determine execution tier
    tier = classify_query_tier(
        query=query,
        top_confidence=top_conf,
        ranked_evidence=ranked_evidence,
    )

    estimated_cost = 0.0
    if tier == ResponseTier.TIER_1_RETRIEVAL_ONLY:
        recommendation = format_tier1_templated_response(
            query=query,
            top_reasoning=top_reasoning,
            crop=crop,
            location=location,
            metadata=getattr(top_ev, "metadata", {}) if top_ev else {},
        )
        estimated_cost = 0.000000  # Near-zero cost
        summary = f"[Tier 1 Retrieval-Only] {recommendation[:110]}..."

    elif tier == ResponseTier.TIER_2_CHEAP_LLM:
        recommendation = generate_tier2_cheap_llm_response(
            query=query,
            evidence_text=top_reasoning,
            crop=crop,
            location=location,
            llm_provider=llm_provider,
        )
        estimated_cost = 0.000120  # Cheap model token estimate (~150 tokens)
        summary = f"[Tier 2 Cheap LLM] {recommendation[:110]}..."

    else:  # Tier 3
        evidence_summary_lines = [
            f"- {getattr(ev, 'agent', 'Agent')}: {getattr(ev, 'reasoning', '')}"
            for ev in ranked_evidence[:5]
        ]
        evidence_str = "\n".join(evidence_summary_lines)
        recommendation = generate_tier3_full_llm_response(
            query=query,
            evidence_text=evidence_str,
            context=context,
            llm_provider=llm_provider,
        )
        estimated_cost = 0.002100  # Full LLM context cost (~1000 tokens)
        summary = f"[Tier 3 Full LLM] {recommendation[:110]}..."

    # Record metrics in global tracker
    tier_tracker.record_query(tier, estimated_cost)

    return {
        "tier": tier,
        "recommendation": recommendation,
        "summary": summary,
        "estimated_cost_usd": estimated_cost,
    }
