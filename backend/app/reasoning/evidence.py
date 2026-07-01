"""
Kisan Mitra AI — Evidence Collector & Ranking Engine
======================================================
Implements:
  - EvidenceCollector: Validates, filters, and de-duplicates incoming evidence.
  - EvidenceRankingEngine: Scores and ranks evidence using a weighted multi-factor
    signal: agent confidence × freshness decay × source trust × relevance.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.reasoning.core import ReasoningContext
from app.schemas.evidence import BaseEvidence

logger = logging.getLogger("kisan_mitra_ai.reasoning.evidence")

# ---------------------------------------------------------------------------
# Source Trust Weights — empirically calibrated per source system.
# ---------------------------------------------------------------------------
_SOURCE_TRUST: dict[str, float] = {
    "OpenWeatherAPI": 0.90,
    "IMD": 0.95,
    "AgMarknet": 0.92,
    "Mandi": 0.88,
    "AgriKB": 0.85,
    "RAG": 0.80,
    "Farmer": 0.70,
    "Memory": 0.75,
    "Default": 0.65,
}

# Freshness half-life in seconds (evidence decays after this period)
_FRESHNESS_HALF_LIFE_SECONDS: float = 3 * 3600.0  # 3 hours


# ---------------------------------------------------------------------------
# Evidence Collector
# ---------------------------------------------------------------------------

class EvidenceCollector:
    """
    Validates, filters, and de-duplicates raw evidence items coming from
    specialist agents. Returns a clean evidence set for ranking.
    """

    def __init__(self, min_confidence: float = 0.10) -> None:
        self.min_confidence = min_confidence
        self._stats: dict[str, int] = {
            "received": 0, "invalid": 0, "low_confidence": 0, "duplicates": 0, "accepted": 0
        }

    def collect(
        self,
        evidence_items: list[BaseEvidence],
        ctx: ReasoningContext,
    ) -> list[BaseEvidence]:
        """
        Filters and de-duplicates evidence items.
        Returns only valid, high-confidence, unique items.
        """
        accepted: list[BaseEvidence] = []
        seen_ids: set[str] = set()

        for ev in evidence_items:
            self._stats["received"] += 1

            if ev.validation_state == "invalid":
                self._stats["invalid"] += 1
                logger.debug(f"[EvidenceCollector] Skipping invalid evidence: {ev.id}")
                continue

            if ev.confidence < self.min_confidence:
                self._stats["low_confidence"] += 1
                logger.debug(
                    f"[EvidenceCollector] Skipping low-confidence evidence: {ev.id} "
                    f"(conf={ev.confidence:.2f})"
                )
                continue

            if ev.id in seen_ids:
                self._stats["duplicates"] += 1
                logger.debug(f"[EvidenceCollector] Deduplicating evidence: {ev.id}")
                continue

            seen_ids.add(ev.id)
            accepted.append(ev)
            self._stats["accepted"] += 1

        logger.info(
            f"[EvidenceCollector] Collected {self._stats['accepted']}/{self._stats['received']} "
            f"items (invalid={self._stats['invalid']}, "
            f"low_conf={self._stats['low_confidence']}, "
            f"dupes={self._stats['duplicates']})"
        )
        return accepted

    @property
    def stats(self) -> dict[str, int]:
        return dict(self._stats)


# ---------------------------------------------------------------------------
# Ranked Evidence
# ---------------------------------------------------------------------------

class RankedEvidence(BaseEvidence):
    """
    Wraps a BaseEvidence with composite ranking signal.
    Adds computed scores so downstream engines can make consistent decisions.
    """
    composite_score: float = 0.0
    freshness_score: float = 1.0
    trust_score: float = 0.65
    relevance_score: float = 1.0
    rank: int = 0


# ---------------------------------------------------------------------------
# Evidence Ranking Engine
# ---------------------------------------------------------------------------

class EvidenceRankingEngine:
    """
    Scores and ranks collected evidence using a multi-factor composite signal:

        composite = confidence_weight × trust_weight × freshness_decay × relevance_signal

    Higher composite scores indicate more reliable, timely, trustworthy evidence.
    The ranking is deterministic given the same inputs.
    """

    def __init__(
        self,
        confidence_weight: float = 0.40,
        trust_weight: float = 0.30,
        freshness_weight: float = 0.20,
        relevance_weight: float = 0.10,
    ) -> None:
        self.w_confidence = confidence_weight
        self.w_trust = trust_weight
        self.w_freshness = freshness_weight
        self.w_relevance = relevance_weight

    def _freshness_score(self, ev: BaseEvidence) -> float:
        """Exponential decay — evidence older than 3 hours loses significant weight."""
        age_seconds = time.time() - ev.timestamp
        return float(0.5 ** (age_seconds / _FRESHNESS_HALF_LIFE_SECONDS))

    def _trust_score(self, ev: BaseEvidence) -> float:
        """Source-calibrated trust score with a fallback default."""
        return float(_SOURCE_TRUST.get(ev.source, _SOURCE_TRUST["Default"]))

    def _relevance_score(self, ev: BaseEvidence, ctx: ReasoningContext) -> float:
        """
        Heuristic relevance — boosts evidence that is contextually aligned with
        the crop and location signals present in the reasoning context.
        """
        score = 1.0
        if ctx.crop and any(ctx.crop.lower() in str(v).lower() for v in ev.metadata.values()):
            score += 0.15
        if ctx.location and any(ctx.location.lower() in str(v).lower() for v in ev.metadata.values()):
            score += 0.10
        return min(score, 1.5)

    def _composite(
        self, ev: BaseEvidence, freshness: float, trust: float, relevance: float
    ) -> float:
        raw = (
            self.w_confidence * ev.confidence
            + self.w_trust * trust
            + self.w_freshness * freshness
            + self.w_relevance * min(relevance, 1.0)
        )
        return round(min(raw, 1.0), 4)

    def rank(
        self,
        evidence_items: list[BaseEvidence],
        ctx: ReasoningContext,
    ) -> list[RankedEvidence]:
        """
        Returns a ranked list of RankedEvidence objects, highest composite score first.
        """
        ranked: list[RankedEvidence] = []

        for ev in evidence_items:
            freshness = self._freshness_score(ev)
            trust = self._trust_score(ev)
            relevance = self._relevance_score(ev, ctx)
            composite = self._composite(ev, freshness, trust, relevance)

            ranked_ev = RankedEvidence(
                **ev.model_dump(),
                composite_score=composite,
                freshness_score=freshness,
                trust_score=trust,
                relevance_score=relevance,
            )
            ranked.append(ranked_ev)

        ranked.sort(key=lambda e: e.composite_score, reverse=True)
        for i, ev in enumerate(ranked):
            ev.rank = i + 1

        logger.info(
            f"[EvidenceRankingEngine] Ranked {len(ranked)} items. "
            f"Top score={ranked[0].composite_score if ranked else 0.0:.4f}"
        )
        return ranked

    def summary(self, ranked_evidence: list[RankedEvidence]) -> list[dict[str, Any]]:
        """Returns a serializable summary of ranked evidence for debugging."""
        return [
            {
                "rank": ev.rank,
                "id": ev.id,
                "agent": ev.agent,
                "source": ev.source,
                "confidence": ev.confidence,
                "composite_score": ev.composite_score,
                "freshness_score": ev.freshness_score,
                "trust_score": ev.trust_score,
                "relevance_score": ev.relevance_score,
            }
            for ev in ranked_evidence
        ]
