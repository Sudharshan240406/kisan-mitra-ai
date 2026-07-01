"""
Kisan Mitra AI — Confidence Engine
=====================================
Advanced multi-signal confidence estimator for the Reasoning Platform.

Supersedes the legacy `ConfidenceAggregator` in `app.intelligence.confidence`.
Produces a rich `ConfidenceReport` with:
  - Per-agent confidence breakdown
  - Evidence ensemble confidence (weighted average over composite scores)
  - Missing-field penalty scaling
  - Evidence coverage bonus (more sources = higher confidence floor)
  - Uncertainty bounds (min/max credible interval)
  - Calibration flags for downstream explainability
"""
from __future__ import annotations

import logging
from typing import Any

from app.reasoning.evidence import RankedEvidence
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.reasoning.confidence")

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
_PENALTY_PER_MISSING_FIELD: float = 0.08     # Per missing field penalty
_MAX_PENALTY: float = 0.40                   # Capped total penalty
_COVERAGE_BONUS_PER_AGENT: float = 0.03      # Bonus per additional distinct agent
_MAX_COVERAGE_BONUS: float = 0.15            # Capped coverage bonus
_CONFIDENCE_FLOOR: float = 0.05             # Minimum achievable overall confidence


# ---------------------------------------------------------------------------
# Output Data Model
# ---------------------------------------------------------------------------

class ConfidenceReport(BaseModel):
    """
    Comprehensive confidence report produced by the ConfidenceEngine.
    Extends the legacy ConfidenceReport with composite and uncertainty fields.
    """
    # Per-entity breakdowns
    per_agent_confidence: dict[str, float] = Field(
        ..., description="Mean confidence per contributing agent."
    )
    per_evidence_composite: dict[str, float] = Field(
        ..., description="Composite score per evidence item ID."
    )

    # Aggregate signals
    ensemble_confidence: float = Field(
        ..., description="Weighted ensemble confidence over all ranked evidence."
    )
    coverage_bonus: float = Field(
        ..., description="Bonus awarded for multi-source evidence coverage."
    )
    missing_penalty: float = Field(
        ..., description="Total confidence penalty for missing query fields."
    )
    overall_confidence: float = Field(
        ..., description="Final net confidence score (0.0 to 1.0)."
    )

    # Credible interval
    confidence_lower: float = Field(
        ..., description="Lower bound of credible confidence interval."
    )
    confidence_upper: float = Field(
        ..., description="Upper bound of credible confidence interval."
    )

    # Calibration
    high_confidence: bool = Field(
        ..., description="True when overall confidence >= 0.70."
    )
    calibration_flags: list[str] = Field(
        default_factory=list,
        description="List of calibration warnings (e.g. 'low_evidence_count')."
    )

    # Compatibility shim for legacy consumers
    @property
    def decision_confidence(self) -> float:
        return self.ensemble_confidence

    @property
    def agent_confidences(self) -> dict[str, float]:
        return self.per_agent_confidence


# ---------------------------------------------------------------------------
# Confidence Engine
# ---------------------------------------------------------------------------

class ConfidenceEngine:
    """
    Advanced confidence estimator for the AI Reasoning Platform.

    Computes a multi-signal confidence report from ranked evidence, applying:
      - Weighted ensemble averaging over composite scores
      - Source-coverage bonus for multi-agent evidence breadth
      - Missing-field penalty for incomplete queries
      - Uncertainty interval estimation
      - Calibration quality flags
    """

    def __init__(
        self,
        penalty_per_missing: float = _PENALTY_PER_MISSING_FIELD,
        max_penalty: float = _MAX_PENALTY,
        coverage_bonus_per_agent: float = _COVERAGE_BONUS_PER_AGENT,
        max_coverage_bonus: float = _MAX_COVERAGE_BONUS,
        confidence_floor: float = _CONFIDENCE_FLOOR,
    ) -> None:
        self.penalty_per_missing = penalty_per_missing
        self.max_penalty = max_penalty
        self.coverage_bonus_per_agent = coverage_bonus_per_agent
        self.max_coverage_bonus = max_coverage_bonus
        self.confidence_floor = confidence_floor

    def _per_agent_confidence(
        self, ranked: list[RankedEvidence]
    ) -> dict[str, float]:
        """Computes mean confidence per contributing agent."""
        from collections import defaultdict
        agent_sums: dict[str, list[float]] = defaultdict(list)
        for ev in ranked:
            agent_sums[ev.agent].append(ev.confidence)
        return {
            agent: round(sum(vals) / len(vals), 4)
            for agent, vals in agent_sums.items()
        }

    def _ensemble_confidence(self, ranked: list[RankedEvidence]) -> float:
        """Weighted average confidence using composite scores as weights."""
        if not ranked:
            return 0.0
        total_weight = sum(ev.composite_score for ev in ranked)
        if total_weight == 0.0:
            return 0.0
        weighted_sum = sum(ev.confidence * ev.composite_score for ev in ranked)
        return round(weighted_sum / total_weight, 4)

    def _coverage_bonus(self, ranked: list[RankedEvidence]) -> float:
        """Bonus based on the number of distinct agents contributing evidence."""
        distinct_agents = len({ev.agent for ev in ranked})
        bonus = min((distinct_agents - 1) * self.coverage_bonus_per_agent, self.max_coverage_bonus)
        return round(max(bonus, 0.0), 4)

    def _missing_penalty(self, missing_fields: list[str]) -> float:
        """Calculates total penalty capped at max_penalty."""
        penalty = min(len(missing_fields) * self.penalty_per_missing, self.max_penalty)
        return round(penalty, 4)

    def _credible_interval(
        self, overall: float, ranked: list[RankedEvidence]
    ) -> tuple[float, float]:
        """Computes a simple credible interval using evidence score spread."""
        if not ranked:
            return (0.0, 0.0)
        scores = [ev.composite_score for ev in ranked]
        spread = (max(scores) - min(scores)) / 2.0
        lower = round(max(overall - spread, 0.0), 4)
        upper = round(min(overall + spread, 1.0), 4)
        return (lower, upper)

    def _calibration_flags(
        self,
        ranked: list[RankedEvidence],
        missing_fields: list[str],
        ensemble: float,
    ) -> list[str]:
        """Detects calibration quality issues and returns warning flags."""
        flags: list[str] = []
        if len(ranked) < 2:
            flags.append("low_evidence_count")
        if len({ev.agent for ev in ranked}) < 2:
            flags.append("single_agent_only")
        if missing_fields:
            flags.append(f"missing_fields:{len(missing_fields)}")
        if ensemble < 0.40:
            flags.append("low_ensemble_confidence")
        if any(ev.freshness_score < 0.50 for ev in ranked):
            flags.append("stale_evidence_present")
        return flags

    def estimate(
        self,
        ranked_evidence: list[RankedEvidence],
        missing_fields: list[str],
    ) -> ConfidenceReport:
        """
        Produces the full ConfidenceReport from ranked evidence.
        """
        per_agent = self._per_agent_confidence(ranked_evidence)
        per_ev_composite = {ev.id: ev.composite_score for ev in ranked_evidence}
        ensemble = self._ensemble_confidence(ranked_evidence)
        coverage = self._coverage_bonus(ranked_evidence)
        penalty = self._missing_penalty(missing_fields)

        boosted = min(ensemble + coverage, 1.0)
        overall = round(max(boosted - penalty, self.confidence_floor), 4)

        lower, upper = self._credible_interval(overall, ranked_evidence)
        flags = self._calibration_flags(ranked_evidence, missing_fields, ensemble)

        report = ConfidenceReport(
            per_agent_confidence=per_agent,
            per_evidence_composite=per_ev_composite,
            ensemble_confidence=ensemble,
            coverage_bonus=coverage,
            missing_penalty=penalty,
            overall_confidence=overall,
            confidence_lower=lower,
            confidence_upper=upper,
            high_confidence=overall >= 0.70,
            calibration_flags=flags,
        )
        logger.info(
            f"[ConfidenceEngine] overall={overall:.3f} "
            f"(ensemble={ensemble:.3f}, bonus={coverage:.3f}, penalty={penalty:.3f}) "
            f"flags={flags}"
        )
        return report

    def health(self) -> dict[str, Any]:
        return {"status": "healthy", "component": "ConfidenceEngine"}
