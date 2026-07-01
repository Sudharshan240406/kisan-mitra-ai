"""
Unit Tests — Reasoning Platform (Step 10C)
============================================
Tests cover all core reasoning sub-systems:
  - ReasoningPlatform (core)
  - EvidenceCollector & EvidenceRankingEngine
  - ConfidenceEngine
  - ConsensusEngine & ConflictResolutionEngine
  - DecisionSynthesizer & ExplainabilityEngine
  - HumanEscalationEngine
  - ReasoningTelemetry
"""
from __future__ import annotations

import time
import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.reasoning.confidence import ConfidenceEngine, ConfidenceReport
from app.reasoning.consensus import ConflictResolutionEngine, ConsensusEngine
from app.reasoning.core import (
    ReasoningCache,
    ReasoningContext,
    ReasoningMetrics,
    ReasoningPlatform,
    ReasoningRegistry,
    ReasoningSession,
)
from app.reasoning.chief import ChiefReasoningAgent
from app.reasoning.escalation import HumanEscalationEngine
from app.reasoning.evidence import EvidenceCollector, EvidenceRankingEngine, RankedEvidence
from app.reasoning.synthesis import DecisionSynthesizer, ExplainabilityEngine
from app.reasoning.telemetry import ReasoningTelemetry
from app.schemas.evidence import BaseEvidence


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_evidence(
    agent: str = "Weather",
    source: str = "OpenWeatherAPI",
    confidence: float = 0.85,
    weight: float = 1.0,
    reasoning: str = "Rainfall expected in next 24 hours.",
    validation_state: str = "valid",
    metadata: dict[str, Any] | None = None,
    age_seconds: float = 0.0,
) -> BaseEvidence:
    ev = BaseEvidence(
        id=f"EV-{uuid.uuid4().hex[:8]}",
        source=source,
        agent=agent,
        confidence=confidence,
        weight=weight,
        reasoning=reasoning,
        validation_state=validation_state,
        metadata=metadata or {},
    )
    if age_seconds > 0:
        ev.timestamp = time.time() - age_seconds
    return ev


def make_context(
    query: str = "What should I do for my wheat crop?",
    crop: str | None = "wheat",
    location: str | None = "Punjab",
) -> ReasoningContext:
    return ReasoningContext(
        session_id="CTX-test",
        trace_id="TR-test",
        request_id="REQ-test",
        query=query,
        crop=crop,
        location=location,
    )


def make_conf_report(overall: float = 0.75, missing: list[str] | None = None) -> ConfidenceReport:
    return ConfidenceReport(
        per_agent_confidence={"W": overall},
        per_evidence_composite={"ev1": 0.80},
        ensemble_confidence=overall,
        coverage_bonus=0.05,
        missing_penalty=0.05 * len(missing or []),
        overall_confidence=overall,
        confidence_lower=max(overall - 0.1, 0.0),
        confidence_upper=min(overall + 0.1, 1.0),
        high_confidence=overall >= 0.70,
        calibration_flags=[],
    )


# ---------------------------------------------------------------------------
# ReasoningCore Tests
# ---------------------------------------------------------------------------

class TestReasoningSession:
    def test_complete(self) -> None:
        session = ReasoningSession(session_id="S1", trace_id="T1")
        time.sleep(0.005)  # Ensure measurable elapsed time
        session.complete(confidence=0.85)
        assert session.status == "completed"
        assert session.confidence == 0.85
        assert session.end_time is not None
        assert session.duration_ms >= 0

    def test_fail(self) -> None:
        session = ReasoningSession(session_id="S2", trace_id="T2")
        session.fail("timeout")
        assert session.status == "failed"
        assert session.metadata["failure_reason"] == "timeout"

    def test_escalate(self) -> None:
        session = ReasoningSession(session_id="S3", trace_id="T3")
        session.escalate()
        assert session.status == "escalated"
        assert session.escalated is True


class TestReasoningCache:
    def test_set_and_get(self) -> None:
        cache = ReasoningCache(max_size=10, ttl_seconds=60)
        cache.set("query1", {"result": "ok"})
        result = cache.get("query1")
        assert result == {"result": "ok"}

    def test_cache_miss(self) -> None:
        cache = ReasoningCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiry(self) -> None:
        cache = ReasoningCache(ttl_seconds=0.01)
        cache.set("q", "v")
        time.sleep(0.05)
        assert cache.get("q") is None

    def test_eviction_at_max_size(self) -> None:
        cache = ReasoningCache(max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        assert len(cache._store) == 2

    def test_hit_ratio(self) -> None:
        cache = ReasoningCache()
        cache.set("x", 1)
        cache.get("x")
        cache.get("missing")
        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_ratio"] == 0.5


class TestReasoningRegistry:
    def test_register_and_get(self) -> None:
        reg = ReasoningRegistry()
        component = MagicMock()
        reg.register("test_comp", component)
        assert reg.get("test_comp") is component

    def test_get_missing_raises(self) -> None:
        reg = ReasoningRegistry()
        with pytest.raises(KeyError):
            reg.get("nonexistent")

    def test_list_components(self) -> None:
        reg = ReasoningRegistry()
        reg.register("a", MagicMock())
        reg.register("b", MagicMock())
        assert set(reg.list_components()) == {"a", "b"}


class TestReasoningPlatform:
    def test_create_session(self) -> None:
        platform = ReasoningPlatform()
        session = platform.create_session(trace_id="TR-001", query="test query")
        assert session.trace_id == "TR-001"
        assert session.status == "running"
        assert session.session_id.startswith("RSN-")

    def test_complete_session(self) -> None:
        platform = ReasoningPlatform()
        session = platform.create_session("TR-002", "query")
        platform.complete_session(session, confidence=0.75, evidence_count=5, consensus_success=True)
        assert session.status == "completed"
        assert platform.metrics.completed_sessions == 1

    def test_health(self) -> None:
        platform = ReasoningPlatform()
        health = platform.health()
        assert health["status"] == "healthy"
        assert "cache_stats" in health
        assert "metrics" in health

    def test_complete_session_preserves_escalated_status(self) -> None:
        platform = ReasoningPlatform()
        session = platform.create_session("TR-003", "query")
        session.escalate()
        platform.complete_session(session, confidence=0.20, evidence_count=0, consensus_success=False)
        assert session.status == "escalated"
        assert session.confidence == 0.20
        assert platform.metrics.escalated_sessions == 1


# ---------------------------------------------------------------------------
# EvidenceCollector Tests
# ---------------------------------------------------------------------------

class TestEvidenceCollector:
    def test_filters_invalid(self) -> None:
        collector = EvidenceCollector()
        ctx = make_context()
        ev_valid = make_evidence(validation_state="valid")
        ev_invalid = make_evidence(validation_state="invalid")
        result = collector.collect([ev_valid, ev_invalid], ctx)
        assert len(result) == 1
        assert result[0].validation_state == "valid"

    def test_filters_low_confidence(self) -> None:
        collector = EvidenceCollector(min_confidence=0.5)
        ctx = make_context()
        ev_high = make_evidence(confidence=0.9)
        ev_low = make_evidence(confidence=0.1)
        result = collector.collect([ev_high, ev_low], ctx)
        assert len(result) == 1
        assert result[0].confidence == 0.9

    def test_deduplicates(self) -> None:
        collector = EvidenceCollector()
        ctx = make_context()
        ev = make_evidence()
        result = collector.collect([ev, ev], ctx)
        assert len(result) == 1

    def test_stats(self) -> None:
        collector = EvidenceCollector()
        ctx = make_context()
        collector.collect([make_evidence(), make_evidence(validation_state="invalid")], ctx)
        assert collector.stats["received"] == 2
        assert collector.stats["invalid"] == 1
        assert collector.stats["accepted"] == 1


# ---------------------------------------------------------------------------
# EvidenceRankingEngine Tests
# ---------------------------------------------------------------------------

class TestEvidenceRankingEngine:
    def test_ranking_order(self) -> None:
        engine = EvidenceRankingEngine()
        ctx = make_context()
        ev_high = make_evidence(confidence=0.95, source="IMD")
        ev_low = make_evidence(confidence=0.40, source="Farmer")
        ranked = engine.rank([ev_low, ev_high], ctx)
        assert ranked[0].composite_score >= ranked[1].composite_score
        assert ranked[0].rank == 1

    def test_freshness_decay(self) -> None:
        engine = EvidenceRankingEngine()
        ctx = make_context()
        fresh = make_evidence(confidence=0.80, age_seconds=0)
        stale = make_evidence(confidence=0.80, age_seconds=3 * 3600)
        ranked = engine.rank([fresh, stale], ctx)
        assert ranked[0].freshness_score >= ranked[1].freshness_score

    def test_relevance_boost(self) -> None:
        engine = EvidenceRankingEngine()
        ctx = make_context(crop="wheat", location="Punjab")
        with_crop = make_evidence(metadata={"crop": "wheat"})
        without = make_evidence(metadata={})
        ranked = engine.rank([without, with_crop], ctx)
        crop_ranked = next(e for e in ranked if "wheat" in e.metadata.get("crop", ""))
        assert crop_ranked.relevance_score > 1.0

    def test_composite_capped_at_one(self) -> None:
        engine = EvidenceRankingEngine()
        ctx = make_context()
        ev = make_evidence(confidence=1.0, source="IMD")
        ranked = engine.rank([ev], ctx)
        assert ranked[0].composite_score <= 1.0

    def test_summary(self) -> None:
        engine = EvidenceRankingEngine()
        ctx = make_context()
        ev = make_evidence()
        ranked = engine.rank([ev], ctx)
        summary = engine.summary(ranked)
        assert len(summary) == 1
        assert "composite_score" in summary[0]


# ---------------------------------------------------------------------------
# ConfidenceEngine Tests
# ---------------------------------------------------------------------------

class TestConfidenceEngine:
    def _make_ranked(self, confidence: float, agent: str = "W", composite: float = 0.8) -> RankedEvidence:
        ev = make_evidence(agent=agent, confidence=confidence)
        return RankedEvidence(
            **ev.model_dump(),
            composite_score=composite,
            freshness_score=0.9,
            trust_score=0.85,
            relevance_score=1.0,
        )

    def test_overall_confidence_basic(self) -> None:
        engine = ConfidenceEngine()
        ranked = [self._make_ranked(0.85)]
        report = engine.estimate(ranked, missing_fields=[])
        assert 0.0 < report.overall_confidence <= 1.0

    def test_missing_penalty_reduces_confidence(self) -> None:
        engine = ConfidenceEngine()
        ranked = [self._make_ranked(0.85)]
        no_missing = engine.estimate(ranked, [])
        with_missing = engine.estimate(ranked, ["crop", "location", "season"])
        assert with_missing.overall_confidence < no_missing.overall_confidence

    def test_coverage_bonus(self) -> None:
        engine = ConfidenceEngine()
        single = [self._make_ranked(0.80, agent="W")]
        multi = [
            self._make_ranked(0.80, agent="W"),
            self._make_ranked(0.75, agent="M"),
            self._make_ranked(0.70, agent="K"),
        ]
        single_report = engine.estimate(single, [])
        multi_report = engine.estimate(multi, [])
        assert multi_report.coverage_bonus > single_report.coverage_bonus

    def test_calibration_flags(self) -> None:
        engine = ConfidenceEngine()
        single = [self._make_ranked(0.30)]
        report = engine.estimate(single, ["crop"])
        assert any(
            flag in report.calibration_flags
            for flag in ["low_evidence_count", "low_ensemble_confidence", "missing_fields:1"]
        )

    def test_credible_interval(self) -> None:
        engine = ConfidenceEngine()
        ranked = [self._make_ranked(0.9, composite=0.9), self._make_ranked(0.5, composite=0.5)]
        report = engine.estimate(ranked, [])
        assert report.confidence_lower <= report.overall_confidence <= report.confidence_upper

    def test_high_confidence_flag(self) -> None:
        engine = ConfidenceEngine()
        ranked = [
            self._make_ranked(0.95, composite=0.95),
            self._make_ranked(0.90, composite=0.90),
        ]
        report = engine.estimate(ranked, [])
        assert report.high_confidence is True


# ---------------------------------------------------------------------------
# ConsensusEngine Tests
# ---------------------------------------------------------------------------

class TestConsensusEngine:
    def _make_ranked_with_score(self, composite: float, agent: str = "A") -> RankedEvidence:
        ev = make_evidence(agent=agent)
        return RankedEvidence(**ev.model_dump(), composite_score=composite)

    def test_consensus_reached(self) -> None:
        engine = ConsensusEngine()
        items = [self._make_ranked_with_score(0.80), self._make_ranked_with_score(0.82)]
        result = engine.evaluate(items)
        assert result["reached"] is True

    def test_consensus_not_reached(self) -> None:
        engine = ConsensusEngine()
        # spread = 0.95 - 0.05 = 0.90; variance = (0.225^2 * 2) / 2 = 0.101... > 0.10
        items = [self._make_ranked_with_score(0.95), self._make_ranked_with_score(0.05)]
        result = engine.evaluate(items)
        assert result["reached"] is False

    def test_single_item_defaults_to_consensus(self) -> None:
        engine = ConsensusEngine()
        result = engine.evaluate([self._make_ranked_with_score(0.7)])
        assert result["reached"] is True


# ---------------------------------------------------------------------------
# ConflictResolutionEngine Tests
# ---------------------------------------------------------------------------

class TestConflictResolutionEngine:
    def _make_scored(self, composite: float, agent: str = "W", trust: float = 0.8) -> RankedEvidence:
        ev = make_evidence(agent=agent)
        return RankedEvidence(
            **ev.model_dump(),
            composite_score=composite,
            trust_score=trust,
            freshness_score=0.9,
        )

    def test_no_conflict(self) -> None:
        engine = ConflictResolutionEngine()
        items = [self._make_scored(0.80), self._make_scored(0.82)]
        conflicts, resolutions = engine.resolve(items)
        assert conflicts == []
        assert resolutions == []

    def test_conflict_detected(self) -> None:
        engine = ConflictResolutionEngine()
        items = [
            self._make_scored(0.90, agent="Weather"),
            self._make_scored(0.40, agent="Weather"),
        ]
        conflicts, resolutions = engine.resolve(items)
        assert len(conflicts) > 0
        assert len(resolutions) > 0

    def test_invalid_evidence_conflict(self) -> None:
        engine = ConflictResolutionEngine()
        valid_ev = self._make_scored(0.80)
        invalid_ev = make_evidence(validation_state="invalid")
        invalid_ranked = RankedEvidence(**invalid_ev.model_dump(), composite_score=0.3)
        conflicts, resolutions = engine.resolve([valid_ev, invalid_ranked])
        assert any("invalid" in c.lower() or "validation" in c.lower() for c in conflicts)


# ---------------------------------------------------------------------------
# DecisionSynthesizer Tests
# ---------------------------------------------------------------------------

class TestDecisionSynthesizer:
    def _make_ranked(self, agent: str, composite: float, confidence: float = 0.85) -> RankedEvidence:
        ev = make_evidence(agent=agent, confidence=confidence)
        r = RankedEvidence(
            **ev.model_dump(),
            composite_score=composite,
            freshness_score=0.85,
            trust_score=0.80,
            relevance_score=1.0,
            rank=1,
        )
        return r

    @pytest.mark.asyncio
    async def test_synthesize_returns_all_keys(self) -> None:
        synth = DecisionSynthesizer()
        ctx = make_context()
        ranked = [self._make_ranked("Weather", 0.85)]
        conf = make_conf_report()
        result = await synth.synthesize(ranked, ctx, conf)
        assert "primary_recommendation" in result
        assert "alternatives" in result
        assert "risk_assessment" in result
        assert "suggested_actions" in result
        assert "reasoning_path" in result

    @pytest.mark.asyncio
    async def test_empty_evidence_returns_critical(self) -> None:
        synth = DecisionSynthesizer()
        ctx = make_context()
        conf = make_conf_report(overall=0.0)
        result = await synth.synthesize([], ctx, conf)
        assert result["risk_assessment"]["risk_level"] == "critical"


# ---------------------------------------------------------------------------
# HumanEscalationEngine Tests
# ---------------------------------------------------------------------------

class TestHumanEscalationEngine:
    def test_no_escalation_needed(self) -> None:
        engine = HumanEscalationEngine()
        escalated, reason, packet = engine.evaluate(
            confidence=0.80,
            conflicts=[],
            missing_fields=[],
            warnings=[],
            trace_id="TR-100",
            query="How to irrigate wheat?",
            evidence_count=2,
        )
        assert escalated is False
        assert reason is None
        assert packet is None

    def test_low_confidence_triggers_escalation(self) -> None:
        engine = HumanEscalationEngine(confidence_threshold=0.50)
        escalated, reason, packet = engine.evaluate(
            confidence=0.20,
            conflicts=[],
            missing_fields=[],
            warnings=[],
            trace_id="TR-101",
            query="generic query",
            evidence_count=2,
        )
        assert escalated is True
        assert reason is not None
        assert packet is not None
        assert packet["routing"]["target"] == "KVK_EXPERT_QUEUE"

    def test_safety_keyword_triggers_escalation(self) -> None:
        engine = HumanEscalationEngine()
        escalated, reason, _ = engine.evaluate(
            confidence=0.90,
            conflicts=[],
            missing_fields=[],
            warnings=["Warning: possible pesticide overdose"],
            trace_id="TR-102",
            query="crop question",
            evidence_count=2,
        )
        assert escalated is True
        assert reason is not None
        assert "pesticide overdose" in reason.lower()

    def test_too_many_missing_fields(self) -> None:
        engine = HumanEscalationEngine(max_missing_fields=2)
        escalated, reason, _ = engine.evaluate(
            confidence=0.85,
            conflicts=[],
            missing_fields=["crop", "location", "season"],
            warnings=[],
            trace_id="TR-103",
            query="query",
            evidence_count=2,
        )
        assert escalated is True

    def test_low_evidence_count_triggers_escalation(self) -> None:
        engine = HumanEscalationEngine(min_evidence_count=2)
        escalated, reason, packet = engine.evaluate(
            confidence=0.85,
            conflicts=[],
            missing_fields=[],
            warnings=[],
            trace_id="TR-104",
            query="query",
            evidence_count=0,
        )
        assert escalated is True
        assert reason is not None
        assert packet is not None

    def test_escalation_counter(self) -> None:
        engine = HumanEscalationEngine(confidence_threshold=0.90)
        for _ in range(3):
            engine.evaluate(0.10, [], [], [], "T", "q", 1)
        assert engine.escalation_count == 3


class TestChiefReasoningAgent:
    @pytest.mark.asyncio
    async def test_reasoning_result_exposes_calibration_flags(self) -> None:
        platform = ReasoningPlatform()
        chief = ChiefReasoningAgent(platform)
        result = await chief.reason(
            query="Will it rain?",
            trace_id="TR-chief",
            request_id="REQ-chief",
            parsed_evidence=[make_evidence(agent="Weather", confidence=0.30)],
            missing_fields=["location"],
        )
        assert "low_evidence_count" in result.calibration_flags
        assert result.confidence_interval[0] <= result.overall_confidence <= result.confidence_interval[1]


# ---------------------------------------------------------------------------
# ReasoningTelemetry Tests
# ---------------------------------------------------------------------------

class TestReasoningTelemetry:
    def test_record_completed(self) -> None:
        tel = ReasoningTelemetry()
        tel.record("S1", "T1", 250.0, 5, 0.80, True, False)
        metrics = tel.aggregate_metrics()
        assert metrics["total_sessions"] == 1
        assert metrics["avg_duration_ms"] == 250.0
        assert metrics["avg_confidence"] == 0.80

    def test_record_escalation(self) -> None:
        tel = ReasoningTelemetry()
        tel.record("S2", "T2", 100.0, 2, 0.20, False, True)
        metrics = tel.aggregate_metrics()
        assert metrics["total_escalations"] == 1
        assert metrics["escalation_rate"] == 1.0

    def test_record_failure(self) -> None:
        tel = ReasoningTelemetry()
        tel.record_failure("S3", "T3", "Timeout during reasoning")
        assert tel._total_events == 1

    def test_recent_events(self) -> None:
        tel = ReasoningTelemetry()
        for i in range(5):
            tel.record(f"S{i}", f"T{i}", 100.0, 3, 0.70, True, False)
        events = tel.recent_events(limit=3)
        assert len(events) == 3
        assert "event_type" in events[0]

    def test_buffer_max(self) -> None:
        tel = ReasoningTelemetry(max_buffer=5)
        for i in range(10):
            tel.record(f"S{i}", f"T{i}", 50.0, 1, 0.5, True, False)
        assert len(tel._events) <= 5
