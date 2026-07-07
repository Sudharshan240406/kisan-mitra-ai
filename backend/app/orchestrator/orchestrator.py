import logging
import time
import uuid
import asyncio
from typing import Any, Dict, List

from app.channels.envelope import MessageEnvelope, ResponseEnvelope
from app.core.container import Container
from app.core.context import AgentContext
from app.core.event_bus import Event
from app.core.exceptions import OrchestratorException

# Orchestrator Core Modules
from app.orchestrator.router import IntentRouter
from app.orchestrator.planner import DynamicPlanner
from app.orchestrator.validator import ResponseValidator
from app.orchestrator.response_builder import ResponseBuilder

# Memory Engine Integration
from app.memory.memory_engine import FarmerMemoryEngine

# Schemas
from app.schemas.requests import ExecutionRequest, AgentRequest
from app.schemas.responses import StandardResponse, TrustedRecommendation, AgentResult
from app.schemas.evidence import BaseEvidence
from app.utils.id import generate_trace_id, generate_uuid

logger = logging.getLogger("kisan_mitra_ai")

class AgentOrchestrator:
    """
    Intelligent AI Orchestrator that coordinates all agricultural specialists.
    Performs intent detection, dynamically selects agents, executes them in parallel,
    runs response validation, and returns structured recommendations.
    """
    def __init__(self, container: Container) -> None:
        self.container = container
        self.router = IntentRouter()
        self.planner = DynamicPlanner()
        self.validator = ResponseValidator()
        self.builder = ResponseBuilder()
        self.memory_engine = FarmerMemoryEngine()

        logger.info("AgentOrchestrator initialized with intent-routing and dynamic planner.")

    async def execute_query(self, request: ExecutionRequest) -> StandardResponse:
        start_time = time.time()
        trace_id = generate_trace_id()
        request_id = generate_uuid()

        # 1. Memory Retrieval (Task 3 / Task 6)
        farmer_id = request.farmer_id or (
            request.session_id
            if request.session_id in ("farmer_ramesh", "farmer_siddappa")
            else None
        )
        
        lang = "en"
        location = "Punjab"
        crop = "Wheat"
        
        if farmer_id:
            try:
                # Retrieve from memory engine (Task 6)
                mem_data = self.memory_engine.retrieve_memory(farmer_id)
                profile = mem_data.get("profile")
                if profile:
                    lang = profile.get("preferred_language", "en")
                    location = f"{profile.get('district', 'Ludhiana')}, {profile.get('state', 'Punjab')}"
                    crop_hist = profile.get("crop_history", [])
                    if crop_hist:
                        crop = crop_hist[0]
            except Exception as e:
                logger.warning(f"[MemoryRetrieval] Profile fetch failed from memory engine: {e}")

        context = AgentContext(
            request_id=request_id,
            trace_id=trace_id,
            session_id=request.session_id,
            farmer_id=farmer_id,
            language=lang
        )
        context.metadata["container"] = self.container
        context.metadata["crop"] = crop
        context.metadata["location"] = location

        logger.info(f"[Orchestrator] Query received: '{request.query[:35]}'")

        self.container.event_bus.publish(Event(
            event_type="query_received",
            trace_id=trace_id,
            request_id=request_id,
            session_id=request.session_id,
            payload={"query": request.query}
        ))

        try:
            # 2. Intent Detection (Task 2)
            intent_data = self.router.detect_intent(request.query)
            logger.info(f"[IntentDetection] Intent: {intent_data['intent']} | Confidence: {intent_data['confidence']}")

            # 3. Dynamic Agent Selection (Task 4)
            selected_agents = self.planner.select_agents(intent_data["intent"])
            logger.info(f"[Planner] Selected agents for task execution: {selected_agents}")

            self.container.event_bus.publish(Event(
                event_type="planning_completed",
                trace_id=trace_id,
                request_id=request_id,
                session_id=request.session_id,
                payload={"workflow_id": intent_data["intent"], "steps": selected_agents}
            ))

            # 4. Parallel Execution (Task 5)
            agent_tasks = []
            active_called_agents = []
            
            for agent_name in selected_agents:
                # LLM is invoked during Reasoning, we execute specific specialists
                if agent_name == "LLM":
                    continue
                try:
                    agent = self.container.registry.get(agent_name)
                except Exception:
                    agent = None
                
                if agent:
                    req = AgentRequest(query=request.query)
                    agent_tasks.append(agent.execute(req, context))
                    active_called_agents.append(agent_name)

            results = await asyncio.gather(*agent_tasks, return_exceptions=True)

            # 5. Compile Evidence & Call Chief Reasoning Agent
            evidence_items = []
            
            # Inject memory evidence
            if farmer_id:
                try:
                    mem_ev = self.container.adaptive_recommender.generate_personalization_evidence(farmer_id, context)
                    if mem_ev:
                        evidence_items.append(mem_ev)
                except Exception as mem_err:
                    logger.warning(f"Memory evidence injection failed: {mem_err}")

            for agent_name, result in zip(active_called_agents, results):
                if isinstance(result, Exception):
                    logger.error(f"Agent {agent_name} execution threw exception: {result}")
                    continue
                
                # Parse to BaseEvidence
                if result.evidence:
                    for ev_dict in result.evidence:
                        ev_dict.setdefault("id", f"EV-{uuid.uuid4().hex[:8]}")
                        ev_dict.setdefault("source", agent_name)
                        ev_dict.setdefault("agent", agent_name)
                        ev_dict.setdefault("reasoning", result.content[:120])
                        ev_dict.setdefault("confidence", result.confidence)
                        try:
                            evidence_items.append(BaseEvidence(**ev_dict))
                        except Exception as parse_err:
                            logger.warning(f"Could not parse evidence dict: {parse_err}")
                else:
                    evidence_items.append(BaseEvidence(
                        id=f"EV-{uuid.uuid4().hex[:8]}",
                        source=agent_name,
                        agent=agent_name,
                        timestamp=time.time(),
                        confidence=result.confidence,
                        weight=1.0,
                        reasoning=result.content[:200],
                        metadata=result.metrics
                    ))

            # Trigger reasoning consensus
            reasoning_result = await self.container.chief_agent.reason(
                query=request.query,
                trace_id=trace_id,
                request_id=request_id,
                parsed_evidence=evidence_items,
                missing_fields=intent_data["entities"],
                agent_context=context,
                language=lang,
                crop=crop,
                location=location
            )

            risk_score = reasoning_result.risk_assessment.risk_score if hasattr(reasoning_result.risk_assessment, "risk_score") else 0.0

            # 6. Response Validation (Task 6)
            rec_dict = self.builder.build_trusted_recommendation(
                summary=reasoning_result.summary,
                recommendation=reasoning_result.primary_recommendation,
                confidence=reasoning_result.overall_confidence,
                reasoning=reasoning_result.reasoning_path,
                sources=list({ev.get("source", "") for ev in reasoning_result.evidence_used}),
                evidence=reasoning_result.evidence_used,
                warnings=reasoning_result.warnings,
                missing_information=reasoning_result.missing_information,
                follow_up_required=reasoning_result.suggested_actions,
                safety_assessment={
                    "risk_score": risk_score,
                    "consensus_reached": reasoning_result.consensus_reached,
                    "conflicts_detected": reasoning_result.conflicts_detected,
                    "conflicts_resolved": reasoning_result.conflicts_resolved,
                    "escalated": reasoning_result.escalated
                },
                reasoning_graph_ref=reasoning_result.reasoning_graph_ref or reasoning_result.result_id
            )

            validation_warnings = self.validator.validate(rec_dict)
            rec_dict["warnings"].extend(validation_warnings)

            # 7. Tracing & Telemetry (Task 8)
            duration_ms = (time.time() - start_time) * 1000.0
            
            logger.info(
                f"[ExecutionTrace] ID: {request_id} | Agents Called: {active_called_agents} | "
                f"Latency: {duration_ms:.1f}ms | Errors: None"
            )

            self.container.metrics.record(
                name="execution_latency",
                value=duration_ms,
                trace_id=trace_id,
                session_id=request.session_id
            )

            # Update Persistent Memory Engine (Task 10)
            if farmer_id:
                try:
                    recommended_schemes = []
                    if "pm-kisan" in reasoning_result.primary_recommendation.lower() or "scheme" in reasoning_result.primary_recommendation.lower():
                        recommended_schemes = ["pm-kisan"]
                    self.memory_engine.save_memory(
                        farmer_id=farmer_id,
                        question=request.query,
                        intent=intent_data["intent"],
                        response=reasoning_result.primary_recommendation,
                        confidence=reasoning_result.overall_confidence,
                        execution_id=request_id,
                        recommended_schemes=recommended_schemes,
                        applied_schemes=None,
                        rejected_schemes=None,
                        completed_schemes=None,
                        documents_requested=reasoning_result.missing_information,
                        documents_submitted=None
                    )
                    logger.info(f"[Orchestrator] Saved interaction turn to Persistent Memory Engine for: {farmer_id}")
                except Exception as mem_err:
                    logger.warning(f"[Orchestrator] Failed to save turn to memory engine: {mem_err}")

            # Append memory log
            if farmer_id:
                try:
                    memory_svc = self.container.personalization_platform.registry.get("long_term_memory")
                    memory_svc.log_conversation(
                        farmer_id=farmer_id,
                        query=request.query,
                        response=reasoning_result.primary_recommendation
                    )
                except Exception as mem_log_err:
                    logger.warning(f"Memory logging failed: {mem_log_err}")

            recommendation = TrustedRecommendation.model_validate(rec_dict)

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
                session_id=request.session_id
            )

            logger.error(f"[OrchestratorException] Trace: {trace_id} | Error: {e}")
            raise OrchestratorException(f"Orchestration failure: {e!s}")

    async def execute_envelope(self, envelope: MessageEnvelope) -> ResponseEnvelope:
        """
        Executes messaging envelopes while preserving full schema structures.
        """
        query_text = envelope.payload.get("text") or envelope.payload.get("query") or ""
        
        exec_req = ExecutionRequest(
            session_id=envelope.conversation_id,
            query=query_text,
            farmer_id=envelope.sender if envelope.sender != "system" else None
        )
        
        try:
            std_res = await self.execute_query(exec_req)
            return ResponseEnvelope(
                message_id=envelope.message_id,
                conversation_id=envelope.conversation_id,
                channel=envelope.channel,
                receiver=envelope.sender,
                language=envelope.language,
                payload=std_res.data,
                trace_id=envelope.trace_id or generate_trace_id(),
                status="success"
            )
        except Exception as e:
            return ResponseEnvelope(
                message_id=envelope.message_id,
                conversation_id=envelope.conversation_id,
                channel=envelope.channel,
                receiver=envelope.sender,
                language=envelope.language,
                payload={"error": str(e)},
                trace_id=envelope.trace_id or generate_trace_id(),
                status="failed"
            )

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "orchestrator_version": "v3.0-rc",
            "event_bus": self.container.event_bus.health(),
            "metrics": self.container.metrics.health()
        }
