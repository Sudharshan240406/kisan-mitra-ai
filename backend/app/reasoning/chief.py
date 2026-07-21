"""
Kisan Mitra AI — Chief Reasoning Agent
========================================
The ChiefReasoningAgent is the master coordinator of the multi-agent
reasoning pipeline. It:

  1. Creates a reasoning context and session from an incoming query.
  2. Formulates an agent execution plan based on detected intents.
  3. Delegates evidence gathering to the EvidenceCollector.
  4. Invokes the EvidenceRankingEngine to prioritize findings.
  5. Calls the ConfidenceEngine to produce explainable confidence scores.
  6. Passes ranked evidence to the DecisionSynthesizer for recommendation.
  7. Runs the ConsensusEngine to verify multi-agent agreement.
  8. Invokes ConflictResolutionEngine on detected contradictions.
  9. Triggers HumanEscalation when safety / confidence thresholds are breached.
 10. Builds and returns the final ReasoningResult payload.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

from app.core.context import AgentContext
from app.reasoning.core import ReasoningContext, ReasoningPlatform
from app.schemas.evidence import BaseEvidence
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.reasoning.chief")


# ---------------------------------------------------------------------------
# ReasoningResult — the authoritative output of the platform
# ---------------------------------------------------------------------------

class AlternativeRecommendation(BaseModel):
    """A ranked alternative to the primary recommendation."""
    rank: int = Field(..., description="Alternative rank position (1 = best alternative).")
    summary: str = Field(..., description="Brief summary of this alternative path.")
    rationale: str = Field(..., description="Reasoning explaining why this is secondary.")
    confidence: float = Field(..., description="Confidence of this alternative recommendation.")
    trade_offs: list[str] = Field(default_factory=list, description="Known trade-offs vs primary recommendation.")


class RiskAssessment(BaseModel):
    """Structured risk profile attached to the primary recommendation."""
    risk_score: float = Field(..., description="Overall risk score (0.0 = safe, 1.0 = critical).")
    risk_level: str = Field(..., description="Human-readable risk level: low | medium | high | critical.")
    risk_factors: list[str] = Field(default_factory=list, description="Specific risk factors identified.")
    mitigation_steps: list[str] = Field(default_factory=list, description="Suggested steps to reduce risk.")


class ReasoningResult(BaseModel):
    """
    The final, authoritative output of the Reasoning Platform. This is the
    only artifact that must leave the reasoning layer — no raw agent output
    is returned directly to the user.
    """
    result_id: str = Field(..., description="Unique reasoning result identifier.")
    session_id: str = Field(..., description="Associated reasoning session identifier.")
    trace_id: str = Field(..., description="Distributed trace identifier.")
    query: str = Field(..., description="Original query under evaluation.")

    # Primary advisory output
    primary_recommendation: str = Field(..., description="The main consolidated advisory recommendation.")
    summary: str = Field(..., description="One-sentence summary of the advisory.")
    suggested_actions: list[str] = Field(default_factory=list, description="Concrete, actionable next steps.")

    # Ranked alternatives
    alternatives: list[AlternativeRecommendation] = Field(
        default_factory=list, description="Alternative recommendations ranked by confidence."
    )

    # Risk and safety
    risk_assessment: RiskAssessment = Field(..., description="Structured risk profile.")
    warnings: list[str] = Field(default_factory=list, description="Safety or policy warnings.")
    missing_information: list[str] = Field(default_factory=list, description="Missing query fields.")

    # Evidence and confidence
    evidence_used: list[dict[str, Any]] = Field(default_factory=list, description="Serialized evidence records used.")
    overall_confidence: float = Field(..., description="Overall reasoning confidence (0.0 to 1.0).")
    per_agent_confidence: dict[str, float] = Field(
        default_factory=dict, description="Per-agent confidence scores."
    )
    confidence_interval: tuple[float, float] = Field(
        default=(0.0, 0.0), description="Lower and upper confidence bounds."
    )
    calibration_flags: list[str] = Field(
        default_factory=list, description="Calibration warnings from the confidence engine."
    )

    # Explainability
    explanation: str = Field(..., description="Human-readable explanation of the recommendation.")
    reasoning_path: list[str] = Field(default_factory=list, description="Step-by-step reasoning trace.")
    agents_contributing: list[str] = Field(default_factory=list, description="Agents that contributed evidence.")
    assumptions: list[str] = Field(default_factory=list, description="Assumptions made during reasoning.")

    # Consensus
    consensus_reached: bool = Field(default=True, description="Whether agents reached consensus.")
    conflicts_detected: list[str] = Field(default_factory=list, description="Detected inter-agent conflicts.")
    conflicts_resolved: list[str] = Field(default_factory=list, description="How conflicts were resolved.")

    # Escalation
    escalated: bool = Field(default=False, description="Whether human escalation was triggered.")
    escalation_reason: Optional[str] = Field(default=None, description="Reason for escalation if triggered.")
    escalation_packet: Optional[dict[str, Any]] = Field(default=None, description="Structured escalation payload.")

    # Graph ref
    reasoning_graph_ref: Optional[str] = Field(default=None, description="Reference to the reasoning graph.")
    timestamp: float = Field(default_factory=time.time, description="Result creation timestamp.")


# ---------------------------------------------------------------------------
# ChiefReasoningAgent
# ---------------------------------------------------------------------------

class ChiefReasoningAgent:
    """
    The Chief Reasoning Agent (CRA) is the supreme coordinator of the
    Kisan Mitra AI Reasoning Platform. It orchestrates all specialist
    sub-agents, compiles evidence, resolves conflicts, ensures consensus,
    and synthesizes the final explainable recommendation.

    The CRA is the ONLY component authorized to produce a final advisory
    recommendation visible to the farmer or downstream channels.
    """

    def __init__(self, platform: ReasoningPlatform) -> None:
        self.platform = platform
        self._escalation_log: list[dict[str, Any]] = []
        logger.info("[ChiefReasoningAgent] Chief Reasoning Agent initialized.")

    def _get_component(self, name: str, factory: Any) -> Any:
        try:
            return self.platform.registry.get(name)
        except KeyError:
            component = factory()
            self.platform.registry.register(name, component)
            return component

    def _build_context(
        self,
        query: str,
        trace_id: str,
        request_id: str,
        agent_outputs: dict[str, Any],
        missing_fields: list[str],
        language: str = "en",
        crop: Optional[str] = None,
        location: Optional[str] = None,
        farmer_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ReasoningContext:
        """Constructs a ReasoningContext from raw orchestrator state."""
        return ReasoningContext(
            session_id=f"CTX-{uuid.uuid4().hex[:8]}",
            trace_id=trace_id,
            request_id=request_id,
            query=query,
            language=language,
            crop=crop,
            location=location,
            farmer_id=farmer_id,
            agent_outputs=agent_outputs,
            missing_fields=missing_fields,
            metadata=metadata or {},
        )

    def _infer_agent_plan(self, query: str, agent_outputs: dict[str, Any]) -> list[str]:
        """
        Infers which specialist agents contributed based on available
        agent output keys and basic keyword signals in the query.
        """
        plan = list(agent_outputs.keys())
        query_lower = query.lower()
        if "weather" in query_lower and "Weather" not in plan:
            plan.append("Weather")
        if any(kw in query_lower for kw in ["price", "mandi", "market"]) and "Market" not in plan:
            plan.append("Market")
        if any(kw in query_lower for kw in ["disease", "rust", "blight", "fungus"]) and "Knowledge" not in plan:
            plan.append("Knowledge")
        if any(kw in query_lower for kw in ["scheme", "subsidy", "kisan"]) and "GovernmentScheme" not in plan:
            plan.append("GovernmentScheme")
        return plan

    async def reason(
        self,
        query: str,
        trace_id: str,
        request_id: str,
        parsed_evidence: list[BaseEvidence],
        missing_fields: list[str],
        agent_context: Optional[AgentContext] = None,
        language: str = "en",
        crop: Optional[str] = None,
        location: Optional[str] = None,
    ) -> ReasoningResult:
        """
        Primary reasoning entrypoint. Executes the full reasoning pipeline
        and returns a ReasoningResult containing the synthesized advisory,
        confidence scores, explanations, and escalation state.
        """
        from app.reasoning.confidence import ConfidenceEngine
        from app.reasoning.consensus import ConflictResolutionEngine, ConsensusEngine
        from app.reasoning.escalation import HumanEscalationEngine
        from app.reasoning.evidence import EvidenceCollector, EvidenceRankingEngine
        from app.reasoning.synthesis import DecisionSynthesizer, ExplainabilityEngine
        from app.reasoning.telemetry import ReasoningTelemetry

        # Query reasoning cache first
        cached_result = self.platform.cache.get(query, language)
        if cached_result:
            logger.info(f"[CRA] Caching system hit for query: '{query[:40]}'")
            return cached_result

        session = self.platform.create_session(trace_id, query)
        result_id = f"RES-{uuid.uuid4().hex[:8].upper()}"
        start_time = time.time()

        agent_outputs = {ev.agent: ev.model_dump() for ev in parsed_evidence}
        farmer_id = agent_context.farmer_id if agent_context else None
        meta_dict = agent_context.metadata if agent_context else {}
        ctx = self._build_context(
            query=query,
            trace_id=trace_id,
            request_id=request_id,
            agent_outputs=agent_outputs,
            missing_fields=missing_fields,
            language=language,
            crop=crop,
            location=location,
            farmer_id=farmer_id,
            metadata=meta_dict,
        )
        ctx.agent_plan = self._infer_agent_plan(query, agent_outputs)
        session.stages_completed.append("context_built")
        logger.info(f"[CRA] Session {session.session_id} | Plan: {ctx.agent_plan}")

        # ── Stage 1: Evidence Collection ──────────────────────────────────
        collector = self._get_component("evidence_collector", EvidenceCollector)
        collected = collector.collect(parsed_evidence, ctx)
        session.stages_completed.append("evidence_collected")

        # ── Stage 2: Evidence Ranking ─────────────────────────────────────
        ranker = self._get_component("evidence_ranker", EvidenceRankingEngine)
        ranked_evidence = ranker.rank(collected, ctx)
        session.stages_completed.append("evidence_ranked")

        # ── Stage 3: Confidence Estimation ───────────────────────────────
        conf_engine = self._get_component("confidence_engine", ConfidenceEngine)
        conf_report = conf_engine.estimate(ranked_evidence, missing_fields)
        session.stages_completed.append("confidence_estimated")

        # ── Stage 4: Consensus Check ──────────────────────────────────────
        consensus_engine = self._get_component("consensus_engine", ConsensusEngine)
        consensus_result = consensus_engine.evaluate(ranked_evidence)
        session.stages_completed.append("consensus_evaluated")

        # ── Stage 5: Conflict Resolution ──────────────────────────────────
        conflict_engine = self._get_component("conflict_resolution_engine", ConflictResolutionEngine)
        conflicts, resolutions = conflict_engine.resolve(ranked_evidence)
        session.stages_completed.append("conflicts_resolved")

        # ── Stage 6: Decision Synthesis ───────────────────────────────────
        synthesizer = self._get_component("decision_synthesizer", DecisionSynthesizer)
        synthesis = await synthesizer.synthesize(ranked_evidence, ctx, conf_report)
        session.stages_completed.append("decision_synthesized")

        # ── Stage 7: Explainability ───────────────────────────────────────
        explainer = self._get_component("explainability_engine", ExplainabilityEngine)
        explanation = explainer.explain(ranked_evidence, synthesis, conf_report, ctx)
        session.stages_completed.append("explanation_generated")

        # ── Stage 8: Human Escalation Check ──────────────────────────────
        escalation_engine = self._get_component("human_escalation_engine", HumanEscalationEngine)
        escalated, escalation_reason, escalation_packet = escalation_engine.evaluate(
            confidence=conf_report.overall_confidence,
            conflicts=conflicts,
            missing_fields=missing_fields,
            warnings=synthesis.get("warnings", []),
            trace_id=trace_id,
            query=query,
            evidence_count=len(ranked_evidence),
        )
        if escalated:
            session.escalate()
            self._escalation_log.append(escalation_packet or {})
        session.stages_completed.append("escalation_checked")

        # ── Stage 9: Reasoning Graph Reference ───────────────────────────
        graph_ref = f"GRAPH-{result_id}"

        # ── Stage 10: Telemetry ───────────────────────────────────────────
        telemetry = self._get_component("reasoning_telemetry", ReasoningTelemetry)
        duration_ms = (time.time() - start_time) * 1000.0
        telemetry.record(
            session_id=session.session_id,
            trace_id=trace_id,
            duration_ms=duration_ms,
            evidence_count=len(ranked_evidence),
            confidence=conf_report.overall_confidence,
            consensus_success=consensus_result.get("reached", True),
            escalated=escalated,
            agent_context=agent_context,
        )

        # Finalize session
        self.platform.complete_session(
            session=session,
            confidence=conf_report.overall_confidence,
            evidence_count=len(ranked_evidence),
            consensus_success=consensus_result.get("reached", True),
        )

        result = ReasoningResult(
            result_id=result_id,
            session_id=session.session_id,
            trace_id=trace_id,
            query=query,
            primary_recommendation=synthesis.get("primary_recommendation", "No recommendation resolved."),
            summary=synthesis.get("summary", ""),
            suggested_actions=synthesis.get("suggested_actions", []),
            alternatives=synthesis.get("alternatives", []),
            risk_assessment=synthesis.get("risk_assessment", RiskAssessment(
                risk_score=0.0, risk_level="low", risk_factors=[], mitigation_steps=[]
            )),
            warnings=synthesis.get("warnings", []) + ([f"CONFLICT: {c}" for c in conflicts]),
            missing_information=missing_fields,
            evidence_used=[ev.model_dump() for ev in ranked_evidence],
            overall_confidence=conf_report.overall_confidence,
            per_agent_confidence=conf_report.per_agent_confidence,
            confidence_interval=(conf_report.confidence_lower, conf_report.confidence_upper),
            calibration_flags=conf_report.calibration_flags,
            explanation=explanation,
            reasoning_path=synthesis.get("reasoning_path", []),
            agents_contributing=list({ev.agent for ev in ranked_evidence}),
            assumptions=synthesis.get("assumptions", []),
            consensus_reached=consensus_result.get("reached", True),
            conflicts_detected=conflicts,
            conflicts_resolved=resolutions,
            escalated=escalated,
            escalation_reason=escalation_reason,
            escalation_packet=escalation_packet,
            reasoning_graph_ref=graph_ref,
        )
        self.platform.cache.set(query, result, language)
        return result

    def get_escalation_log(self) -> list[dict[str, Any]]:
        """Returns the complete escalation packet history."""
        return self._escalation_log

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "platform_metrics": self.platform.metrics.to_dict(),
            "escalations_total": len(self._escalation_log),
        }
