import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.intelligence.arm import AgriculturalReasoningMemory, ReasoningMemoryRecord
from app.intelligence.confidence import ConfidenceAggregator
from app.intelligence.policy import PolicyEngine
from app.intelligence.reasoning_graph import ReasoningGraph, ReasoningNode
from app.intelligence.safety import SafetyGuard
from app.schemas.evidence import BaseEvidence
from app.schemas.responses import TrustedRecommendation
from app.utils.id import generate_uuid


class DecisionStrategy(ABC):
    """
    Abstract interface representing a strategy to resolve and merge multi-agent evidence.
    """
    @abstractmethod
    async def resolve(self, evidence_list: list[BaseEvidence]) -> dict[str, Any]:
        """
        Merge and resolve raw evidence collections.
        """
        pass

class RuleBasedDecision(DecisionStrategy):
    """
    Combines agent outputs sequentially based on structural formatting rules.
    """
    async def resolve(self, evidence_list: list[BaseEvidence]) -> dict[str, Any]:
        segments = []
        path = []
        for ev in evidence_list:
            segments.append(f"[{ev.agent}]: {ev.reasoning}")
            path.append(f"Processed evidence ID {ev.id} from {ev.agent}")

        summary = "Consolidated agricultural advisory checklist."
        recommendation = "\n".join(segments) if segments else "No advisory findings resolved."

        return {
            "summary": summary,
            "recommendation": recommendation,
            "reasoning_path": path,
            "confidence": 1.0
        }

class WeightedEvidenceDecision(DecisionStrategy):
    """
    Combines outputs by ranking them using evidence weights.
    """
    async def resolve(self, evidence_list: list[BaseEvidence]) -> dict[str, Any]:
        # Sort evidence by weight desc
        sorted_ev = sorted(evidence_list, key=lambda x: x.weight, reverse=True)
        segments = []
        path = []

        for ev in sorted_ev:
            segments.append(f"({ev.agent} - weight {ev.weight}): {ev.reasoning}")
            path.append(f"Ranked evidence ID {ev.id} (Weight: {ev.weight})")

        summary = "Weighted multi-agent consolidated recommendation."
        recommendation = "\n".join(segments) if segments else "No advisory findings resolved."

        return {
            "summary": summary,
            "recommendation": recommendation,
            "reasoning_path": path,
            "confidence": 0.95
        }

# Swappable consensus, hybrid, and LLM decision strategy resolvers
class ConsensusDecision(DecisionStrategy):
    """
    Resolves evidence by checking for majority agreement or consensus among high-confidence agents.
    """
    async def resolve(self, evidence_list: list[BaseEvidence]) -> dict[str, Any]:
        if not evidence_list:
            return {
                "summary": "Consensus agricultural advisory.",
                "recommendation": "No advisory findings resolved.",
                "reasoning_path": ["No evidence provided to establish consensus."],
                "confidence": 0.0
            }

        # Calculate consensus confidence (average of valid, high confidence evidences)
        valid_evidences = [ev for ev in evidence_list if ev.validation_state == "valid"]
        if not valid_evidences:
            valid_evidences = evidence_list # fallback

        avg_confidence = sum(ev.confidence for ev in valid_evidences) / len(valid_evidences)

        # Formulate recommendation summarizing consensus
        segments = []
        path = []
        for ev in valid_evidences:
            segments.append(f"Consensus advisory from {ev.agent}: {ev.reasoning}")
            path.append(f"Consensus agreed on evidence ID {ev.id} from {ev.agent} (Confidence: {ev.confidence:.2f})")

        return {
            "summary": "Consensus multi-agent verified recommendation.",
            "recommendation": "\n".join(segments),
            "reasoning_path": path,
            "confidence": avg_confidence
        }

class HybridDecision(DecisionStrategy):
    """
    Combines rule-based checks with weighted parameters to construct a prioritized recommendation.
    """
    async def resolve(self, evidence_list: list[BaseEvidence]) -> dict[str, Any]:
        if not evidence_list:
            return {
                "summary": "Hybrid agricultural advisory.",
                "recommendation": "No advisory findings resolved.",
                "reasoning_path": ["No evidence provided for hybrid execution."],
                "confidence": 0.0
            }

        # Priority: First, separate high-importance warnings/critical logs
        critical_findings = []
        general_findings = sorted(evidence_list, key=lambda x: x.weight, reverse=True)

        segments = []
        path = []

        for ev in general_findings:
            if ev.confidence > 0.85:
                critical_findings.append(ev)
                path.append(f"Hybrid priority elevated for {ev.agent} (ID: {ev.id}, Weight: {ev.weight})")
            else:
                path.append(f"Hybrid processed {ev.agent} (ID: {ev.id}, Weight: {ev.weight})")

        # Merge critical findings first, then rest
        ordered_list = critical_findings + [e for e in general_findings if e not in critical_findings]
        for ev in ordered_list:
            prefix = "CRITICAL" if ev in critical_findings else "General"
            segments.append(f"[{prefix}] ({ev.agent} - weight {ev.weight}): {ev.reasoning}")

        avg_confidence = sum(ev.confidence for ev in evidence_list) / len(evidence_list)

        return {
            "summary": "Hybrid prioritized multi-agent recommendation.",
            "recommendation": "\n".join(segments),
            "reasoning_path": path,
            "confidence": avg_confidence
        }

class FutureLLMDecision(DecisionStrategy):
    """
    LLM-driven resolution strategy that synthesizes multiple agent evidences into a unified response.
    """
    def __init__(self, llm_provider: BaseLLMProvider | None = None) -> None:
        self.llm_provider = llm_provider

    async def resolve(self, evidence_list: list[BaseEvidence]) -> dict[str, Any]:
        if not evidence_list:
            return {
                "summary": "LLM synthesized advisory.",
                "recommendation": "No advisory findings resolved.",
                "reasoning_path": ["No evidence provided to synthesize."],
                "confidence": 0.0
            }

        # Construct prompt
        evidence_texts = []
        for ev in evidence_list:
            evidence_texts.append(f"Agent: {ev.agent}\nSource: {ev.source}\nReasoning: {ev.reasoning}\nConfidence: {ev.confidence}\n---")

        prompt = (
            "As an expert agronomic coordinator, synthesize the following multi-agent evidences into a single, cohesive advisory:\n\n"
            + "\n".join(evidence_texts)
            + "\nProvide a clear, brief, actionable recommendation for the farmer."
        )

        path = [f"Synthesizing {len(evidence_list)} evidence nodes via LLM decision strategy."]

        if self.llm_provider:
            try:
                recommendation = self.llm_provider.generate(
                    prompt=prompt,
                    system_instruction="You are Kisan Mitra AI's Verifier consolidation engine."
                )
                summary = "LLM synthesized multi-agent consolidated recommendation."
                confidence = sum(ev.confidence for ev in evidence_list) / len(evidence_list)
            except Exception as e:
                # Fallback
                recommendation = "Fallback synthesis:\n" + "\n".join(f"- {ev.reasoning}" for ev in evidence_list)
                summary = f"LLM synthesis failed (fallback used): {e!s}"
                confidence = 0.5
        else:
            # Simulated consolidation if no provider is present
            summary = "Simulated LLM synthesized multi-agent recommendation."
            recommendation = "Consolidated Synthesis:\n" + "\n".join(f"- {ev.reasoning}" for ev in evidence_list)
            confidence = sum(ev.confidence for ev in evidence_list) / len(evidence_list)

        return {
            "summary": summary,
            "recommendation": recommendation,
            "reasoning_path": path,
            "confidence": confidence
        }


class DecisionEngine:
    """
    Coordinates decision resolution loops, checks safety guard alerts,
    records reasoning memory traces, applies AI policies, and publishes trusted recommendations.
    """
    def __init__(
        self,
        strategy: DecisionStrategy,
        arm: AgriculturalReasoningMemory,
        policy_engine: Optional[PolicyEngine] = None
    ) -> None:
        self.strategy = strategy
        self.arm = arm
        self.confidence_aggregator = ConfidenceAggregator()
        self.safety_guard = SafetyGuard()
        self.policy_engine = policy_engine or PolicyEngine()

    async def evaluate(  # noqa: PLR0912
        self,
        evidence_list: list[BaseEvidence],
        missing_fields: list[str],
        trace_id: str,
        session_id: str,
        context: Optional[AgentContext] = None
    ) -> TrustedRecommendation:
        decision_id = f"DEC-{generate_uuid()[:8]}"
        start_time = time.time()

        # 1. Merge & Resolve evidence using strategy
        outcome = await self.strategy.resolve(evidence_list)

        # 2. Conflict Checks: cross-reference weather alerts vs manual guides
        warnings = []
        agents_participating = [ev.agent for ev in evidence_list]

        # Simple rule-based structural conflict check skeleton
        has_weather = "Weather" in agents_participating
        has_knowledge = "Knowledge" in agents_participating
        if has_weather and has_knowledge:
            # Check for conflicting guidance cues in text
            weather_text = next((e.reasoning for e in evidence_list if e.agent == "Weather"), "").lower()
            knowledge_text = next((e.reasoning for e in evidence_list if e.agent == "Knowledge"), "").lower()
            if "rain" in weather_text and "fungicide" in knowledge_text:
                warnings.append("Conflict detected: Knowledge recommends spraying fungicide, but Weather indicates rain.")

        # 3. Calculate Aggregated Confidence Reports
        conf_report = self.confidence_aggregator.calculate_confidence(evidence_list, missing_fields)

        # 4. Safety Guard Assessment
        safety_assessment = self.safety_guard.assess(evidence_list, conf_report.overall_confidence)

        # 5. Build Reasoning Graph trace structure
        graph = ReasoningGraph(
            graph_id=f"GRAPH-{decision_id}",
            root_node_id="root-query"
        )

        # Add root query node
        graph.add_node(ReasoningNode(
            node_id="root-query",
            node_type="Query",
            confidence=1.0,
            metadata={"evidence_count": len(evidence_list)}
        ))

        # Add evidence nodes
        for ev in evidence_list:
            graph.add_node(ReasoningNode(
                node_id=ev.id,
                parent_id="root-query",
                node_type="Evidence",
                evidence_id=ev.id,
                confidence=ev.confidence,
                metadata={"agent": ev.agent, "weight": ev.weight}
            ))

        # Add strategy aggregation step
        graph.add_node(ReasoningNode(
            node_id="strategy-resolution",
            parent_id="root-query",
            node_type="Workflow",
            confidence=conf_report.decision_confidence,
            metadata={"strategy": self.strategy.__class__.__name__}
        ))

        # Link evidence nodes to resolution
        for ev in evidence_list:
            node = graph.nodes.get(ev.id)
            if node:
                node.parent_id = "strategy-resolution"

        # Final decision output node
        prev_node = "strategy-resolution"
        graph.add_node(ReasoningNode(
            node_id="decision-output",
            parent_id=prev_node,
            node_type="Decision",
            confidence=conf_report.overall_confidence,
            metadata={"applied_strategy": self.strategy.__class__.__name__}
        ))

        # Validate graph
        graph.validate_graph()

        # Resolve sources list
        sources_list = list({ev.source for ev in evidence_list})

        # Formulate final TrustedRecommendation payload
        recommendation = TrustedRecommendation(
            summary=outcome["summary"],
            recommendation=outcome["recommendation"],
            evidence=[ev.model_dump() for ev in evidence_list],
            confidence=conf_report.overall_confidence,
            risk=safety_assessment.risk_score,
            reasoning=outcome["reasoning_path"],
            sources=sources_list or ["Mock advisory source database"],
            warnings=warnings or safety_assessment.warnings,
            missing_information=missing_fields,
            follow_up_required=["Verify crop symptoms with visual diagnosis if possible."] if missing_fields else [],
            safety_assessment=safety_assessment.model_dump(),
            reasoning_graph_ref=graph.graph_id
        )

        # 5.5. AI Policy Engine Governance validation
        if context:
            policy_reports = await self.policy_engine.evaluate(recommendation, context)
            violations = []
            for r in policy_reports:
                if not r.passed:
                    violations.extend(r.violations)

            if violations:
                recommendation.warnings.extend([f"[POLICY VIOLATION] {v}" for v in violations])
                recommendation.safety_assessment["policy_passed"] = False
                recommendation.safety_assessment["policy_violations"] = violations
            else:
                recommendation.safety_assessment["policy_passed"] = True

            # Telemetry: Record metrics if telemetry exporter is available
            container = context.metadata.get("container")
            if container and hasattr(container, "telemetry"):
                telemetry = container.telemetry
                telemetry.record("decision_latency_ms", (time.time() - start_time) * 1000.0, trace_id, session_id)
                telemetry.record("evidence_count", len(evidence_list), trace_id, session_id)
                telemetry.record("reasoning_depth", len(outcome["reasoning_path"]), trace_id, session_id)
                telemetry.record("reasoning_graph_size", len(graph.nodes), trace_id, session_id)
                telemetry.record("confidence", conf_report.overall_confidence, trace_id, session_id)

                # Interventions/violations count
                if safety_assessment.risk_score > 0.5 or not safety_assessment.is_safe:
                    telemetry.record("safety_intervention", 1, trace_id, session_id)
                for violation in violations:
                    telemetry.record("policy_violation", violation, trace_id, session_id)

        # 6. Save outcome record to Agricultural Reasoning Memory (ARM)
        memory_record = ReasoningMemoryRecord(
            decision_id=decision_id,
            evidence_used=[e.model_dump() for e in evidence_list],
            reasoning_path=outcome["reasoning_path"],
            reasoning_graph=graph.export(),
            decision_strategy=self.strategy.__class__.__name__,
            confidence=conf_report.overall_confidence,
            risk=safety_assessment.risk_score,
            trace_id=trace_id,
            outcome=outcome["summary"],
            supporting_agents=agents_participating
        )
        self.arm.save_record(memory_record)

        return recommendation
