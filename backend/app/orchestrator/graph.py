import json
import logging
from typing import Any, TypedDict

from app.core.context import AgentContext
from app.core.exceptions import OrchestratorException
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult

try:
    from langgraph.graph import END, StateGraph
except ModuleNotFoundError:
    END = "__END__"

    class _CompiledFallbackGraph:
        def __init__(self, entry_point: str, nodes: dict[str, Any], edges: dict[str, str]) -> None:
            self._entry_point = entry_point
            self._nodes = nodes
            self._edges = edges

        async def ainvoke(self, initial_state: dict[str, Any]) -> dict[str, Any]:
            state = dict(initial_state)
            current = self._entry_point

            while current and current != END:
                updates = await self._nodes[current](state)
                if updates:
                    state.update(updates)
                current = self._edges.get(current, END)

            return state

    class StateGraph:  # type: ignore[no-redef]
        def __init__(self, _state_type: type[Any]) -> None:
            self._nodes: dict[str, Any] = {}
            self._edges: dict[str, str] = {}
            self._entry_point: str | None = None

        def add_node(self, name: str, func: Any) -> None:
            self._nodes[name] = func

        def set_entry_point(self, name: str) -> None:
            self._entry_point = name

        def add_edge(self, source: str, target: str) -> None:
            self._edges[source] = target

        def compile(self) -> _CompiledFallbackGraph:
            if self._entry_point is None:
                raise OrchestratorException("Fallback graph compile failed: entry point not set.")
            return _CompiledFallbackGraph(self._entry_point, self._nodes, self._edges)

logger = logging.getLogger("kisan_mitra_ai")

class GraphState(TypedDict):
    """
    State definition passed between the active nodes of the LangGraph execution orchestrator.
    """
    query: str
    context: AgentContext
    plan_steps: list[str]
    agent_results: dict[str, str]  # Maps agent_name -> serialized JSON of AgentResult
    final_response: str | None  # Serialized JSON of UnifiedResponse

# Graph Node Implementations
async def planner_node(state: GraphState) -> dict[str, Any]:
    logger.info("[GraphNode] Entering Planner Node")
    container = state["context"].metadata.get("container")
    if not container:
        raise OrchestratorException("Container instance missing in GraphState metadata.")

    planner = container.registry.get("Planner")
    req = AgentRequest(query=state["query"])
    res: AgentResult = await planner.execute(req, state["context"])

    plan_data = json.loads(res.content)
    steps = plan_data.get("steps", [])

    return {
        "plan_steps": steps,
        "agent_results": {**state["agent_results"], "Planner": res.model_dump_json()}
    }

async def scheduler_node(state: GraphState) -> dict[str, Any]:
    logger.info("[GraphNode] Entering Execution Scheduler Node")
    # Scheduler maps dependency nodes and logs them
    return {}

async def weather_node(state: GraphState) -> dict[str, Any]:
    if "weather" not in state["plan_steps"]:
        return {}
    logger.info("[GraphNode] Entering Weather Agent Node")
    container = state["context"].metadata["container"]
    agent = container.registry.get("Weather")

    req = AgentRequest(query=state["query"])
    res: AgentResult = await agent.execute(req, state["context"])
    return {"agent_results": {**state["agent_results"], "Weather": res.model_dump_json()}}

async def knowledge_node(state: GraphState) -> dict[str, Any]:
    if "disease" not in state["plan_steps"]:  # Sockets knowledge
        return {}
    logger.info("[GraphNode] Entering Knowledge Agent Node")
    container = state["context"].metadata["container"]
    agent = container.registry.get("Knowledge")

    req = AgentRequest(query=state["query"])
    res: AgentResult = await agent.execute(req, state["context"])
    return {"agent_results": {**state["agent_results"], "Knowledge": res.model_dump_json()}}

async def memory_node(state: GraphState) -> dict[str, Any]:
    logger.info("[GraphNode] Entering Memory Agent Node")
    container = state["context"].metadata["container"]
    agent = container.registry.get("Memory")

    req = AgentRequest(query=state["query"])
    res: AgentResult = await agent.execute(req, state["context"])
    return {"agent_results": {**state["agent_results"], "Memory": res.model_dump_json()}}

async def market_node(state: GraphState) -> dict[str, Any]:
    if "market" not in state["plan_steps"]:
        return {}
    logger.info("[GraphNode] Entering Market Agent Node")
    container = state["context"].metadata["container"]
    agent = container.registry.get("Market")

    req = AgentRequest(query=state["query"])
    res: AgentResult = await agent.execute(req, state["context"])
    return {"agent_results": {**state["agent_results"], "Market": res.model_dump_json()}}

async def scheme_node(state: GraphState) -> dict[str, Any]:
    # Run scheme matching if query contains indicators
    if "scheme" not in state["query"].lower() and "welfare" not in state["query"].lower():
        return {}
    logger.info("[GraphNode] Entering GovernmentScheme Agent Node")
    container = state["context"].metadata["container"]
    agent = container.registry.get("GovernmentScheme")

    req = AgentRequest(query=state["query"])
    res: AgentResult = await agent.execute(req, state["context"])
    return {"agent_results": {**state["agent_results"], "GovernmentScheme": res.model_dump_json()}}

async def reasoning_node(state: GraphState) -> dict[str, Any]:
    """
    Reasoning Node — replaces the legacy Verifier node.

    Collects all raw agent results from the graph state, converts them to
    BaseEvidence objects, invokes the ChiefReasoningAgent's 10-stage
    reasoning pipeline, and serializes the resulting ReasoningResult as a
    TrustedRecommendation for the orchestrator.
    """
    import time
    import uuid

    from app.reasoning.chief import ReasoningResult
    from app.schemas.evidence import BaseEvidence
    from app.schemas.responses import TrustedRecommendation

    logger.info("[GraphNode] Entering AI Reasoning Node (ChiefReasoningAgent)")
    container = state["context"].metadata["container"]
    ctx = state["context"]
    missing_fields: list[str] = ctx.metadata.get("missing_fields", [])

    # ── Parse all agent results into BaseEvidence objects ─────────────────
    evidence_items: list[BaseEvidence] = []

    # ── Inject Personalization / Memory Evidence ──────────────────────────
    if ctx.farmer_id:
        try:
            p_ctx = container.personalization_platform.get_personalized_context(ctx.farmer_id)
            if p_ctx:
                if not ctx.metadata.get("crop"):
                    growing_crops = [c.get("crop") for c in p_ctx.twin.crop_history]
                    if growing_crops:
                        ctx.metadata["crop"] = growing_crops[0]
                        ctx.crop = growing_crops[0]
                if not ctx.metadata.get("location"):
                    loc_str = f"{p_ctx.twin.village}, {p_ctx.twin.district}, {p_ctx.twin.state}"
                    ctx.metadata["location"] = loc_str
                    ctx.location = loc_str

                mem_ev = container.adaptive_recommender.generate_personalization_evidence(ctx.farmer_id, ctx)
                if mem_ev:
                    evidence_items.append(mem_ev)
                    logger.info(f"[ReasoningNode] Injected MemoryEvidence for farmer: {ctx.farmer_id}")
        except Exception as p_err:
            logger.warning(f"[ReasoningNode] Personalization injection failed: {p_err}")
    for agent_name, result_json in state["agent_results"].items():
        try:
            result = AgentResult.model_validate_json(result_json)
            if result.evidence:
                for ev_dict in result.evidence:
                    # Ensure required fields exist before constructing
                    ev_dict.setdefault("id", f"EV-{uuid.uuid4().hex[:8]}")
                    ev_dict.setdefault("source", agent_name)
                    ev_dict.setdefault("agent", agent_name)
                    ev_dict.setdefault("reasoning", result.content[:120])
                    ev_dict.setdefault("confidence", result.confidence)
                    try:
                        evidence_items.append(BaseEvidence(**ev_dict))
                    except Exception as parse_err:
                        logger.warning(
                            f"[ReasoningNode] Could not parse evidence dict from '{agent_name}': {parse_err}"
                        )
            else:
                # No structured evidence — build synthetic BaseEvidence from result
                evidence_items.append(BaseEvidence(
                    id=f"EV-{uuid.uuid4().hex[:8]}",
                    source=agent_name,
                    agent=agent_name,
                    timestamp=time.time(),
                    confidence=result.confidence,
                    weight=1.0,
                    reasoning=result.content[:200],
                    metadata=result.metrics,
                ))
        except Exception as e:
            logger.warning(f"[ReasoningNode] Skipping malformed agent result for '{agent_name}': {e}")

    # ── Call ChiefReasoningAgent ──────────────────────────────────────────
    reasoning_result: ReasoningResult = await container.chief_agent.reason(
        query=state["query"],
        trace_id=ctx.trace_id,
        request_id=ctx.request_id,
        parsed_evidence=evidence_items,
        missing_fields=missing_fields,
        agent_context=ctx,
        language=ctx.language or "en",
        crop=ctx.metadata.get("crop"),
        location=ctx.metadata.get("location"),
    )

    # ── Map ReasoningResult → TrustedRecommendation ───────────────────────
    risk_data = reasoning_result.risk_assessment
    risk_score = risk_data.risk_score if hasattr(risk_data, "risk_score") else (
        risk_data.get("risk_score", 0.0) if isinstance(risk_data, dict) else 0.0
    )

    trusted = TrustedRecommendation(
        summary=reasoning_result.summary,
        recommendation=reasoning_result.primary_recommendation,
        evidence=reasoning_result.evidence_used,
        confidence=reasoning_result.overall_confidence,
        risk=risk_score,
        reasoning=reasoning_result.reasoning_path,
        sources=list({ev.get("source", "") for ev in reasoning_result.evidence_used}),
        warnings=reasoning_result.warnings,
        missing_information=reasoning_result.missing_information,
        follow_up_required=reasoning_result.suggested_actions,
        safety_assessment={
            "consensus_reached": reasoning_result.consensus_reached,
            "conflicts_detected": reasoning_result.conflicts_detected,
            "conflicts_resolved": reasoning_result.conflicts_resolved,
            "escalated": reasoning_result.escalated,
            "escalation_reason": reasoning_result.escalation_reason,
            "explanation": reasoning_result.explanation,
            "agents_contributing": reasoning_result.agents_contributing,
            "per_agent_confidence": reasoning_result.per_agent_confidence,
            "confidence_interval": reasoning_result.confidence_interval,
            "calibration_flags": reasoning_result.calibration_flags,
        },
        reasoning_graph_ref=reasoning_result.reasoning_graph_ref or reasoning_result.result_id,
    )

    logger.info(
        f"[ReasoningNode] Reasoning complete: confidence={trusted.confidence:.2f}, "
        f"risk={trusted.risk:.2f}, escalated={reasoning_result.escalated}"
    )
    return {"final_response": trusted.model_dump_json()}


# Build LangGraph StateGraph workflow
workflow = StateGraph(GraphState)

# Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("scheduler", scheduler_node)
workflow.add_node("weather", weather_node)
workflow.add_node("knowledge", knowledge_node)
workflow.add_node("memory", memory_node)
workflow.add_node("market", market_node)
workflow.add_node("scheme", scheme_node)
workflow.add_node("reasoning", reasoning_node)

# Add Edges
workflow.set_entry_point("planner")
workflow.add_edge("planner", "scheduler")
workflow.add_edge("scheduler", "weather")
workflow.add_edge("weather", "knowledge")
workflow.add_edge("knowledge", "memory")
workflow.add_edge("memory", "market")
workflow.add_edge("market", "scheme")
workflow.add_edge("scheme", "reasoning")
workflow.add_edge("reasoning", END)

# Compile graph
compiled_graph = workflow.compile()
