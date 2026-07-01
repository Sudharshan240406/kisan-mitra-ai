import logging
import time
from typing import Any

from app.channels.envelope import MessageEnvelope, ResponseEnvelope
from app.core.container import Container
from app.core.context import AgentContext
from app.core.event_bus import Event
from app.core.exceptions import OrchestratorException

# Intelligence Core Imports
from app.intelligence.analysis import QueryAnalyzer
from app.intelligence.planner import RuleBasedPlanner
from app.orchestrator.graph import GraphState, compiled_graph
from app.orchestrator.scheduler import ExecutionScheduler
from app.schemas.requests import ExecutionRequest
from app.schemas.responses import StandardResponse, TrustedRecommendation
from app.utils.id import generate_trace_id, generate_uuid

logger = logging.getLogger("kisan_mitra_ai")

class AgentOrchestrator:
    """
    Main Orchestrator executing state machine logic.
    Coordinates query execution, registers context tracing variables, and
    orchestrates execution flows via the compiled LangGraph StateGraph.
    """
    def __init__(self, container: Container) -> None:
        self.container = container
        self.scheduler = ExecutionScheduler(container.registry)

        # Initialize Intelligence Core components
        self.analyzer = QueryAnalyzer()
        self.planner = RuleBasedPlanner(self.container.capability_registry)

        logger.info("AgentOrchestrator initialized with Intelligence Core (Analyzer & Planner).")

    async def execute_query(self, request: ExecutionRequest) -> StandardResponse:
        start_time = time.time()
        trace_id = generate_trace_id()
        request_id = generate_uuid()

        # 1. Build unified AgentContext
        farmer_id = request.farmer_id or (
            request.session_id
            if request.session_id in ("farmer_ramesh", "farmer_siddappa")
            else None
        )
        
        # Load language from profile if available
        lang = "en"
        if farmer_id:
            try:
                profile = self.container.personalization_platform.profiles.get(farmer_id)
                if profile:
                    lang = profile.preferred_language
            except Exception:
                pass

        context = AgentContext(
            request_id=request_id,
            trace_id=trace_id,
            session_id=request.session_id,
            farmer_id=farmer_id,
            language=lang
        )

        # Inject container into context metadata for node lookup
        context.metadata["container"] = self.container

        # Set logger contextvars variables
        from app.core.logging_config import request_id_var, session_id_var, trace_id_var
        token_trace = trace_id_var.set(trace_id)
        token_req = request_id_var.set(request_id)
        token_ses = session_id_var.set(request.session_id)

        logger.info(f"[Orchestrator] Ingress query received: '{request.query[:35]}'")

        self.container.event_bus.publish(Event(
            event_type="query_received",
            trace_id=trace_id,
            request_id=request_id,
            session_id=request.session_id,
            payload={"query": request.query}
        ))

        try:
            # 2. Analyze Query & Formulate Execution Plan (Intelligence Core)
            planning_start = time.time()
            analysis = self.analyzer.analyze(request.query)
            plan = await self.planner.plan(analysis)
            planning_duration_ms = (time.time() - planning_start) * 1000.0

            if hasattr(self.container, "telemetry"):
                self.container.telemetry.record(
                    "planning_latency_ms",
                    planning_duration_ms,
                    trace_id,
                    request_id
                )

            # Attach missing fields to context metadata for verifier lookup
            context.metadata["missing_fields"] = analysis.missing_information.missing_fields

            # Every planning decision logs: request_id, trace_id, workflow, entities, intents, complexity, confidence
            logger.info(
                f"[PlanningDecision] Request: {request_id} | Trace: {trace_id} | "
                f"Workflow: {plan.workflow_id} | "
                f"Entities: {analysis.entities.extracted_types} | "
                f"Intents: {analysis.intents.detected_intents} | "
                f"Complexity: {plan.estimated_complexity} | "
                f"Confidence: {analysis.confidence:.2f} | "
                f"Missing: {analysis.missing_information.missing_fields}"
            )

            # Track Planning Metrics in collector
            self.container.metrics.record(
                name="planning_metrics",
                value={
                    "planning_time_ms": planning_duration_ms,
                    "workflow_selected": plan.workflow_id,
                    "intent_count": len(analysis.intents.detected_intents),
                    "entity_count": len(analysis.entities.entities),
                    "confidence": analysis.confidence,
                    "complexity": plan.estimated_complexity,
                    "missing_info": analysis.missing_information.missing_fields
                },
                trace_id=trace_id,
                session_id=request.session_id,
                metadata={"raw_query": request.query}
            )

            self.container.event_bus.publish(Event(
                event_type="planning_completed",
                trace_id=trace_id,
                request_id=request_id,
                session_id=request.session_id,
                payload={"workflow_id": plan.workflow_id, "steps": plan.execution_order}
            ))

            # 3. Invoke compiled LangGraph Workflow
            initial_state: GraphState = {
                "query": request.query,
                "context": context,
                # Translate plan steps dynamically (lowercase mapping for graph routing check)
                "plan_steps": [s.lower() for s in plan.execution_order],
                "agent_results": {},
                "final_response": None
            }

            logger.info(f"[Orchestrator] Initiating LangGraph workflow run ({plan.workflow_id})...")

            self.container.event_bus.publish(Event(
                event_type="graph_execution_started",
                trace_id=trace_id,
                request_id=request_id,
                session_id=request.session_id,
                payload={}
            ))

            # Execute compiled graph state machine
            graph_start = time.time()
            graph_output = await compiled_graph.ainvoke(initial_state)
            workflow_latency = (time.time() - graph_start) * 1000.0

            if hasattr(self.container, "telemetry"):
                self.container.telemetry.record("workflow_latency_ms", workflow_latency, trace_id, request_id)
                self.container.telemetry.record("workflow_execution_time_ms", workflow_latency, trace_id, request_id)
                import sys
                arm_size = sys.getsizeof(self.container.arm._storage)
                self.container.telemetry.record("memory_usage_bytes", arm_size, trace_id, request_id)

            final_res_json = graph_output.get("final_response")
            if not final_res_json:
                raise OrchestratorException("LangGraph workflow finished without returning Verifier output.")

            # Parse output
            recommendation = TrustedRecommendation.model_validate_json(final_res_json)

            # Enrich final response payload metadata with analysis tags
            recommendation.safety_assessment["planning"] = {
                "workflow_id": plan.workflow_id,
                "complexity": plan.estimated_complexity,
                "confidence": analysis.confidence,
                "missing_fields": analysis.missing_information.missing_fields
            }

            duration_ms = (time.time() - start_time) * 1000.0

            # Record execution latency metric
            self.container.metrics.record(
                name="execution_latency",
                value=duration_ms,
                trace_id=trace_id,
                session_id=request.session_id,
                metadata={"plan_depth": len(graph_output.get("plan_steps", []))}
            )

            # Publish completion event
            self.container.event_bus.publish(Event(
                event_type="advisory_generated",
                trace_id=trace_id,
                request_id=request_id,
                session_id=request.session_id,
                payload={"duration_ms": duration_ms}
            ))

            # ── Log interaction to long-term memory if farmer context exists ────
            if context.farmer_id:
                try:
                    memory_svc = self.container.personalization_platform.registry.get("long_term_memory")
                    memory_svc.log_conversation(
                        farmer_id=context.farmer_id,
                        query=request.query,
                        response=recommendation.recommendation
                    )
                    memory_svc.log_recommendation(
                        farmer_id=context.farmer_id,
                        rec_id=f"REC-{request_id[:6].upper()}",
                        text=recommendation.recommendation,
                        confidence=recommendation.confidence
                    )
                    logger.info(f"[Orchestrator] Appended advisory and turn to long-term memory for farmer: {context.farmer_id}")
                except Exception as p_err:
                    logger.warning(f"[Orchestrator] Failed to save personalization logs: {p_err}")

            return StandardResponse(
                status="success",
                data=recommendation.model_dump(),
                execution_time_ms=duration_ms
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            self.container.metrics.record(
                name="error",
                value=str(e),
                trace_id=trace_id,
                session_id=request.session_id,
                metadata={"error_type": type(e).__name__}
            )

            self.container.event_bus.publish(Event(
                event_type="execution_failed",
                trace_id=trace_id,
                request_id=request_id,
                session_id=request.session_id,
                payload={"error": str(e)}
            ))

            logger.error(f"[Orchestrator] Execution failed (Trace: {trace_id}): {e!s}")
            if isinstance(e, OrchestratorException):
                raise e
            raise OrchestratorException(f"Orchestration failure: {e!s}")

        finally:
            # Reset logger contextvars variables
            trace_id_var.reset(token_trace)
            request_id_var.reset(token_req)
            session_id_var.reset(token_ses)

    async def execute_envelope(self, envelope: MessageEnvelope) -> ResponseEnvelope:
        start_time = time.time()
        trace_id = envelope.trace_id or generate_trace_id()
        request_id = envelope.message_id or generate_uuid()
        session_id = envelope.conversation_id

        # Set logger contextvars variables
        from app.core.logging_config import request_id_var, session_id_var, trace_id_var
        token_trace = trace_id_var.set(trace_id)
        token_req = request_id_var.set(request_id)
        token_ses = session_id_var.set(session_id)

        # Extract query text from envelope payload
        query_text = envelope.payload.get("text") or envelope.payload.get("query") or ""

        logger.info(f"[Orchestrator] execute_envelope inbound: '{query_text[:35]}' from channel '{envelope.channel}'")

        # 1. Build unified AgentContext
        envelope_farmer_id = envelope.sender if envelope.sender != "system" else None
        if not envelope_farmer_id and envelope.conversation_id in ("farmer_ramesh", "farmer_siddappa"):
            envelope_farmer_id = envelope.conversation_id

        # Load language from profile if available
        lang = envelope.language.preferred_language or "en"
        if envelope_farmer_id:
            try:
                profile = self.container.personalization_platform.profiles.get(envelope_farmer_id)
                if profile:
                    lang = profile.preferred_language
            except Exception:
                pass

        context = AgentContext(
            request_id=request_id,
            trace_id=trace_id,
            session_id=session_id,
            farmer_id=envelope_farmer_id,
            language=lang
        )
        context.metadata["container"] = self.container
        context.metadata["channel"] = envelope.channel

        self.container.event_bus.publish(Event(
            event_type="query_received",
            trace_id=trace_id,
            request_id=request_id,
            session_id=session_id,
            payload={"query": query_text, "channel": envelope.channel}
        ))

        try:
            # 2. Analyze Query & Formulate Execution Plan (Intelligence Core)
            planning_start = time.time()
            analysis = self.analyzer.analyze(query_text)
            plan = await self.planner.plan(analysis)
            planning_duration_ms = (time.time() - planning_start) * 1000.0

            if hasattr(self.container, "telemetry"):
                self.container.telemetry.record(
                    "planning_latency_ms",
                    planning_duration_ms,
                    trace_id,
                    request_id
                )

            context.metadata["missing_fields"] = analysis.missing_information.missing_fields

            logger.info(
                f"[PlanningDecision] Request: {request_id} | Trace: {trace_id} | "
                f"Workflow: {plan.workflow_id} | "
                f"Complexity: {plan.estimated_complexity} | "
                f"Confidence: {analysis.confidence:.2f}"
            )

            # Track Planning Metrics in collector
            self.container.metrics.record(
                name="planning_metrics",
                value={
                    "planning_time_ms": planning_duration_ms,
                    "workflow_selected": plan.workflow_id,
                    "confidence": analysis.confidence,
                    "complexity": plan.estimated_complexity,
                },
                trace_id=trace_id,
                session_id=session_id
            )

            self.container.event_bus.publish(Event(
                event_type="planning_completed",
                trace_id=trace_id,
                request_id=request_id,
                session_id=session_id,
                payload={"workflow_id": plan.workflow_id, "steps": plan.execution_order}
            ))

            # 3. Invoke compiled LangGraph Workflow
            initial_state: GraphState = {
                "query": query_text,
                "context": context,
                "plan_steps": [s.lower() for s in plan.execution_order],
                "agent_results": {},
                "final_response": None
            }

            logger.info(f"[Orchestrator] Initiating LangGraph workflow run ({plan.workflow_id})...")

            # Execute compiled graph state machine
            graph_output = await compiled_graph.ainvoke(initial_state)

            final_res_json = graph_output.get("final_response")
            if not final_res_json:
                raise OrchestratorException("LangGraph workflow finished without returning Verifier output.")

            recommendation = TrustedRecommendation.model_validate_json(final_res_json)

            # Enrich final response payload metadata
            recommendation.safety_assessment["planning"] = {
                "workflow_id": plan.workflow_id,
                "complexity": plan.estimated_complexity,
                "confidence": analysis.confidence,
            }

            duration_ms = (time.time() - start_time) * 1000.0

            # Record metrics
            self.container.metrics.record(
                name="execution_latency",
                value=duration_ms,
                trace_id=trace_id,
                session_id=session_id
            )

            self.container.event_bus.publish(Event(
                event_type="advisory_generated",
                trace_id=trace_id,
                request_id=request_id,
                session_id=session_id,
                payload={"duration_ms": duration_ms}
            ))

            # ── Log interaction to long-term memory if farmer context exists ────
            if context.farmer_id:
                try:
                    memory_svc = self.container.personalization_platform.registry.get("long_term_memory")
                    memory_svc.log_conversation(
                        farmer_id=context.farmer_id,
                        query=query_text,
                        response=recommendation.recommendation
                    )
                    memory_svc.log_recommendation(
                        farmer_id=context.farmer_id,
                        rec_id=f"REC-{request_id[:6].upper()}",
                        text=recommendation.recommendation,
                        confidence=recommendation.confidence
                    )
                    logger.info(f"[Orchestrator] Appended advisory and turn to long-term memory for farmer: {context.farmer_id}")
                except Exception as p_err:
                    logger.warning(f"[Orchestrator] Failed to save personalization logs: {p_err}")

            # Build ResponseEnvelope
            response_payload = recommendation.model_dump()

            return ResponseEnvelope(
                message_id=envelope.message_id,
                conversation_id=session_id,
                channel=envelope.channel,
                receiver=envelope.sender,
                language=envelope.language,
                payload=response_payload,
                trace_id=trace_id,
                status="success"
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000.0
            self.container.metrics.record(
                name="error",
                value=str(e),
                trace_id=trace_id,
                session_id=session_id
            )

            self.container.event_bus.publish(Event(
                event_type="execution_failed",
                trace_id=trace_id,
                request_id=request_id,
                session_id=session_id,
                payload={"error": str(e)}
            ))

            logger.error(f"[Orchestrator] Execution failed (Trace: {trace_id}): {e!s}")

            return ResponseEnvelope(
                message_id=envelope.message_id,
                conversation_id=session_id,
                channel=envelope.channel,
                receiver=envelope.sender,
                language=envelope.language,
                payload={"error": str(e)},
                trace_id=trace_id,
                status="failed"
            )

        finally:
            # Reset logger contextvars variables
            trace_id_var.reset(token_trace)
            request_id_var.reset(token_req)
            session_id_var.reset(token_ses)

    def health(self) -> dict[str, Any]:
        """
        Exposes health metrics for the Orchestrator.
        """
        return {
            "status": "healthy",
            "scheduler": self.scheduler.health(),
            "event_bus": self.container.event_bus.health(),
            "metrics": self.container.metrics.health()
        }
