"""
Kisan Mitra AI — Decision Synthesizer & Explainability Engine
===============================================================
Two complementary modules:

1. DecisionSynthesizer
   Consolidates ranked evidence, confidence, and context into a structured
   synthesis payload: primary recommendation, alternatives, risk assessment,
   suggested actions, assumptions, and warnings.

2. ExplainabilityEngine
   Produces human-readable explanations of the reasoning process in the
   farmer's preferred language. Applies XAI principles: transparency,
   traceability, uncertainty disclosure.
"""
from __future__ import annotations

import logging
from typing import Any

from app.reasoning.confidence import ConfidenceReport
from app.reasoning.core import ReasoningContext
from app.reasoning.evidence import RankedEvidence

logger = logging.getLogger("kisan_mitra_ai.reasoning.synthesis")

# ---------------------------------------------------------------------------
# Risk categorization thresholds
# ---------------------------------------------------------------------------
_RISK_THRESHOLDS: dict[str, tuple[float, float]] = {
    "low": (0.0, 0.25),
    "medium": (0.25, 0.50),
    "high": (0.50, 0.75),
    "critical": (0.75, 1.01),
}


def _classify_risk(score: float) -> str:
    for level, (lo, hi) in _RISK_THRESHOLDS.items():
        if lo <= score < hi:
            return level
    return "low"


# ---------------------------------------------------------------------------
# DecisionSynthesizer
# ---------------------------------------------------------------------------

class DecisionSynthesizer:
    """
    Synthesizes ranked evidence into the primary advisory recommendation and
    a structured synthesis payload. Uses evidence metadata, confidence report,
    and context to generate actionable, explainable recommendations.

    Synthesis strategy:
      1. Primary recommendation from top-ranked evidence (composite score).
      2. Alternatives derived from the next-highest scoring evidence items.
      3. Risk score: penalise for low confidence, stale evidence, missing fields.
      4. Actions and assumptions extracted from evidence metadata.
      5. Warnings generated from conflict signals and calibration flags.
    """

    async def synthesize(
        self,
        ranked_evidence: list[RankedEvidence],
        ctx: ReasoningContext,
        conf: ConfidenceReport,
    ) -> dict[str, Any]:
        """
        Returns a structured synthesis dict with all advisory components.
        All values are serializable for packing into ReasoningResult.
        """
        if not ranked_evidence:
            return self._empty_synthesis(ctx.query)

        top = ranked_evidence[0]
        rest = ranked_evidence[1:5]  # up to 4 alternatives

        # Primary recommendation
        primary = self._build_primary(top, ctx, conf)

        # Alternatives
        alternatives = [
            self._build_alternative(ev, rank=i + 1, primary_agent=top.agent)
            for i, ev in enumerate(rest)
            if ev.agent != top.agent  # prefer cross-agent alternatives
        ]

        # Risk assessment
        risk_score, risk_factors, mitigation = self._compute_risk(ranked_evidence, conf, ctx)
        risk_level = _classify_risk(risk_score)

        # Suggested actions
        actions = self._extract_actions(ranked_evidence, ctx)

        # Assumptions
        assumptions = self._extract_assumptions(ctx, conf)

        # Warnings
        warnings = self._build_warnings(conf, risk_score)

        # Reasoning path
        reasoning_path = [
            f"[{ev.rank}] {ev.agent} → composite={ev.composite_score:.3f} | conf={ev.confidence:.2f} | {ev.reasoning[:80]}..."
            for ev in ranked_evidence[:6]
        ]

        return {
            "primary_recommendation": primary,
            "summary": f"Based on {len(ranked_evidence)} evidence sources: {primary[:120]}...",
            "alternatives": alternatives,
            "risk_assessment": {
                "risk_score": round(risk_score, 3),
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "mitigation_steps": mitigation,
            },
            "suggested_actions": actions,
            "assumptions": assumptions,
            "warnings": warnings,
            "reasoning_path": reasoning_path,
        }

    def _build_primary(
        self, top: RankedEvidence, ctx: ReasoningContext, conf: ConfidenceReport
    ) -> str:
        crop_ctx = f" for {ctx.crop}" if ctx.crop else ""
        loc_ctx = f" in {ctx.location}" if ctx.location else ""
        confidence_tag = "HIGH" if conf.high_confidence else "MODERATE"

        personalization_tag = ""
        if ctx.farmer_id and "container" in ctx.metadata:
            try:
                container = ctx.metadata["container"]
                p_ctx = container.personalization_platform.get_personalized_context(ctx.farmer_id)
                if p_ctx:
                    avail_budget = p_ctx.profile.budget_limit - p_ctx.profile.budget_spent
                    personalization_tag = (
                        f"[PERSONALIZED FOR {p_ctx.profile.name.upper()}] "
                        f"(Risk: {p_ctx.profile.risk_tolerance.upper()}, Available Budget: {avail_budget:.0f} INR) "
                    )
            except Exception:
                pass

        base_msg = (
            f"[{confidence_tag} CONFIDENCE] Based on {top.agent} evidence{crop_ctx}{loc_ctx}: "
            f"{top.reasoning}. "
            f"Evidence source: {top.source} (trust={top.trust_score:.2f}, "
            f"freshness={top.freshness_score:.2f})."
        )
        return personalization_tag + base_msg

    def _build_alternative(
        self, ev: RankedEvidence, rank: int, primary_agent: str
    ) -> dict[str, Any]:
        return {
            "rank": rank,
            "summary": f"{ev.agent}: {ev.reasoning[:120]}...",
            "rationale": (
                f"Alternative evidence from '{ev.agent}' (composite={ev.composite_score:.3f}). "
                f"Secondary to primary '{primary_agent}' recommendation by composite score."
            ),
            "confidence": ev.confidence,
            "trade_offs": [
                f"Trust={ev.trust_score:.2f} vs primary (consider verifying with local expert).",
                f"Freshness={ev.freshness_score:.2f} — may reflect slightly older conditions.",
            ],
        }

    def _compute_risk(
        self,
        ranked: list[RankedEvidence],
        conf: ConfidenceReport,
        ctx: ReasoningContext,
    ) -> tuple[float, list[str], list[str]]:
        """Computes a risk score from evidence quality signals."""
        risk_score = 0.0
        factors: list[str] = []
        mitigation: list[str] = []

        # Low confidence → higher risk
        if conf.overall_confidence < 0.50:
            risk_score += 0.30
            factors.append("Low overall evidence confidence.")
            mitigation.append("Gather additional crop/location data before acting.")

        # Missing fields → elevated risk
        if ctx.missing_fields:
            delta = min(len(ctx.missing_fields) * 0.08, 0.30)
            risk_score += delta
            factors.append(f"{len(ctx.missing_fields)} query field(s) missing.")
            mitigation.append("Provide complete query (crop, location, season) for accurate advice.")

        # Stale evidence
        stale = [ev for ev in ranked if ev.freshness_score < 0.40]
        if stale:
            risk_score += 0.10
            factors.append(f"{len(stale)} evidence item(s) are stale.")
            mitigation.append("Re-query with fresh data to improve recommendation accuracy.")

        # Single-agent only
        if len({ev.agent for ev in ranked}) < 2:
            risk_score += 0.10
            factors.append("Single agent contributing — limited cross-validation.")
            mitigation.append("Consult a local Krishi Vigyan Kendra (KVK) expert for confirmation.")

        # Personalization risk tolerance adjustment
        if ctx.farmer_id and "container" in ctx.metadata:
            try:
                container = ctx.metadata["container"]
                p_ctx = container.personalization_platform.get_personalized_context(ctx.farmer_id)
                if p_ctx:
                    tolerance = p_ctx.profile.risk_tolerance
                    if tolerance == "low":
                        risk_score += 0.15
                        factors.append("Low farmer risk tolerance context: raised safety thresholds.")
                        mitigation.append("Strictly verify crop parameters and local Mandi trends.")
                    elif tolerance == "high":
                        risk_score = max(0.0, risk_score - 0.10)
            except Exception:
                pass

        return (round(min(risk_score, 1.0), 3), factors, mitigation)

    def _extract_actions(
        self, ranked: list[RankedEvidence], ctx: ReasoningContext
    ) -> list[str]:
        """Extracts concrete suggested actions from evidence metadata."""
        actions: list[str] = []
        seen: set[str] = set()
        for ev in ranked[:5]:
            for key in ("actions", "recommended_steps", "treatment", "suggested_actions"):
                val = ev.metadata.get(key)
                if isinstance(val, list):
                    for a in val:
                        if str(a) not in seen:
                            actions.append(str(a))
                            seen.add(str(a))
                elif isinstance(val, str) and val not in seen:
                    actions.append(val)
                    seen.add(val)
        if not actions:
            crop_str = f" for {ctx.crop}" if ctx.crop else ""
            actions.append(f"Consult local extension officer for advisory{crop_str}.")
        return actions[:8]

    def _extract_assumptions(
        self, ctx: ReasoningContext, conf: ConfidenceReport
    ) -> list[str]:
        assumptions = [
            f"Farmer location assumed: {ctx.location or 'not specified'}.",
            f"Primary crop assumed: {ctx.crop or 'not specified'}.",
        ]
        if conf.missing_penalty > 0:
            assumptions.append(
                f"Confidence penalised by {conf.missing_penalty:.2f} for "
                f"{len(ctx.missing_fields)} missing field(s)."
            )
        return assumptions

    def _build_warnings(
        self, conf: ConfidenceReport, risk_score: float
    ) -> list[str]:
        warnings: list[str] = []
        if not conf.high_confidence:
            warnings.append(
                f"Advisory confidence is {conf.overall_confidence:.0%}. "
                "Verify with a certified agronomy expert before proceeding."
            )
        if risk_score >= 0.50:
            warnings.append(
                f"High risk level detected (score={risk_score:.2f}). "
                "Exercise caution and seek additional expert opinion."
            )
        for flag in conf.calibration_flags:
            warnings.append(f"Calibration flag: {flag}.")
        return warnings

    def _empty_synthesis(self, query: str) -> dict[str, Any]:
        return {
            "primary_recommendation": "Insufficient evidence to provide a recommendation.",
            "summary": f"No evidence was collected for query: {query[:80]}",
            "alternatives": [],
            "risk_assessment": {
                "risk_score": 1.0,
                "risk_level": "critical",
                "risk_factors": ["No evidence collected."],
                "mitigation_steps": ["Retry with complete crop and location information."],
            },
            "suggested_actions": ["Retry with full query context."],
            "assumptions": [],
            "warnings": ["No evidence available — recommendation not possible."],
            "reasoning_path": [],
        }


# ---------------------------------------------------------------------------
# ExplainabilityEngine
# ---------------------------------------------------------------------------

class ExplainabilityEngine:
    """
    Generates human-readable, transparent explanations of the reasoning process.
    Follows XAI (eXplainable AI) principles:
      - Transparency: what evidence was used.
      - Uncertainty disclosure: confidence and interval.
      - Counterfactual hints: what would change the recommendation.
      - Local-language adaptation: inserts crop/location context.
    """

    EXPLANATION_TEMPLATE = (
        "This recommendation is based on {evidence_count} evidence source(s) "
        "from {agent_list}. "
        "The overall confidence is {confidence:.0%} "
        "(range: {lower:.0%}–{upper:.0%}). "
        "{calibration_note}"
        "{conflict_note}"
        "The highest-priority evidence came from '{top_agent}' "
        "(composite score: {top_score:.3f}). "
        "Missing information: {missing}. "
        "To improve confidence, provide: {improve_hint}."
    )

    def explain(
        self,
        ranked_evidence: list[RankedEvidence],
        synthesis: dict[str, Any],
        conf: ConfidenceReport,
        ctx: ReasoningContext,
    ) -> str:
        """
        Produces a structured natural-language explanation string.
        """
        agent_list = list({ev.agent for ev in ranked_evidence})
        top = ranked_evidence[0] if ranked_evidence else None

        calibration_note = ""
        if conf.calibration_flags:
            calibration_note = (
                f"Note: calibration flags detected ({', '.join(conf.calibration_flags)}). "
            )

        risk = synthesis.get("risk_assessment", {})
        conflict_note = ""
        if risk.get("risk_level") in ("high", "critical"):
            conflict_note = (
                f"Risk level is {risk.get('risk_level', 'unknown').upper()}. "
                f"Risk factors: {'; '.join(risk.get('risk_factors', []))}. "
            )

        missing_str = (
            ", ".join(ctx.missing_fields) if ctx.missing_fields else "none"
        )
        improve_hint = (
            "crop name, farmer location, current season"
            if ctx.missing_fields
            else "additional sensor or weather data"
        )

        explanation = self.EXPLANATION_TEMPLATE.format(
            evidence_count=len(ranked_evidence),
            agent_list=", ".join(agent_list) if agent_list else "no agents",
            confidence=conf.overall_confidence,
            lower=conf.confidence_lower,
            upper=conf.confidence_upper,
            calibration_note=calibration_note,
            conflict_note=conflict_note,
            top_agent=top.agent if top else "N/A",
            top_score=top.composite_score if top else 0.0,
            missing=missing_str,
            improve_hint=improve_hint,
        )
        logger.info(f"[ExplainabilityEngine] Generated explanation ({len(explanation)} chars).")
        return explanation
