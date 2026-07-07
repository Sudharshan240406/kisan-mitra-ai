import asyncio
import logging
import time
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.core.container import Container

from app.channels.envelope import MessageEnvelope, ResponseEnvelope
from app.core.context import AgentContext
from app.core.event_bus import Event
from app.core.exceptions import OrchestratorException

# Memory Engine Integration
from app.memory.memory_engine import FarmerMemoryEngine
from app.orchestrator.planner import DynamicPlanner
from app.orchestrator.response_builder import ResponseBuilder

# Orchestrator Core Modules
from app.orchestrator.router import IntentRouter
from app.orchestrator.validator import ResponseValidator
from app.schemas.evidence import BaseEvidence

# Schemas
from app.schemas.requests import AgentRequest, ExecutionRequest
from app.schemas.responses import StandardResponse, TrustedRecommendation
from app.utils.id import generate_trace_id, generate_uuid

logger = logging.getLogger("kisan_mitra_ai")

class AgentOrchestrator:
    """
    Intelligent AI Orchestrator that coordinates all agricultural specialists.
    Performs intent detection, dynamically selects agents, executes them in parallel,
    runs response validation, and returns structured recommendations.
    """
    def __init__(self, container: "Container") -> None:
        self.container = container
        self.router = IntentRouter()
        self.planner = DynamicPlanner()
        self.validator = ResponseValidator()
        self.builder = ResponseBuilder()
        self.memory_engine = FarmerMemoryEngine()
        from app.knowledge_engine.knowledge_engine import KnowledgeEngine
        self.knowledge_engine = KnowledgeEngine()
        self.learning_manager = container.learning_manager
        self.twin_manager = container.twin_manager
        self.autonomous_manager = container.autonomous_manager

        logger.info("AgentOrchestrator initialized with intent-routing and dynamic planner.")

    async def execute_query(self, request: ExecutionRequest) -> StandardResponse:  # noqa: PLR0912
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

            # 2.5. Knowledge Retrieval and Re-ranking (Task 9)
            knowledge_docs = []
            try:
                knowledge_docs = await self.knowledge_engine.retrieve(request.query, context=context)
                logger.info(f"[KnowledgeRetrieval] Retrieved and reranked {len(knowledge_docs)} documents.")
            except Exception as ke_err:
                logger.error(f"[KnowledgeRetrieval] Failed: {ke_err}")

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

            async def execute_agent_with_telemetry(a_name: str, a_obj: Any, a_req: Any, a_ctx: Any) -> Any:
                agent_start = time.time()
                success = False
                retries = 0
                try:
                    res = await a_obj.execute(a_req, a_ctx)
                    success = True
                    return res
                except Exception as ex:
                    logger.warning(f"Agent {a_name} execution failed: {ex}")
                    raise ex
                finally:
                    agent_latency = (time.time() - agent_start) * 1000.0
                    try:
                        self.learning_manager.feedback_engine.record_agent_feedback(
                            agent_name=a_name,
                            success=success,
                            latency_ms=agent_latency,
                            retry_count=retries
                        )
                    except Exception as le_err:
                        logger.warning(f"Failed to log agent feedback for {a_name}: {le_err}")

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
                    agent_tasks.append(execute_agent_with_telemetry(agent_name, agent, req, context))
                    active_called_agents.append(agent_name)

            results = await asyncio.gather(*agent_tasks, return_exceptions=True)

            # 5. Compile Evidence & Call Chief Reasoning Agent
            evidence_items: list[BaseEvidence] = []

            # Load Digital Twin, Run Predictions & Risks (Task 8)
            if farmer_id:
                try:
                    twin = self.twin_manager.get_twin(farmer_id)
                    if twin:
                        # Re-run prediction & risk engine pipelines
                        predictions = self.twin_manager.predict(farmer_id)
                        risks = self.twin_manager.calculate_risk(farmer_id)

                        # Generate proactive recommendations
                        self.twin_manager.generate_recommendations(farmer_id)

                        # Inject DigitalTwinEvidence
                        from app.digital_twin import DigitalTwinEvidence
                        evidence_items.append(DigitalTwinEvidence(
                            id=f"EV-DT-{farmer_id}",
                            source="PredictiveDigitalTwin",
                            agent="DigitalTwinEngine",
                            timestamp=time.time(),
                            confidence=0.4,
                            weight=0.1,
                            reasoning=f"Proactive Next Crop: {predictions.get('next_crop')}. "
                                      f"Water Demand: {predictions.get('water_demand_liters')}L. "
                                      f"Disease Risk: {risks.get('disease_risk')} on predicted {predictions.get('disease_probability', {}).get('disease')}. "
                                      f"Crop Failure Risk: {risks.get('crop_failure_risk')}.",
                            farmer_id=farmer_id,
                            predictions=predictions,
                            risks=risks
                        ))
                except Exception as twin_err:
                    logger.warning(f"[TwinManager] Failed to load/run predictive twin models: {twin_err}")

            # Inject memory evidence
            if farmer_id:
                try:
                    mem_ev = self.container.adaptive_recommender.generate_personalization_evidence(farmer_id, context)
                    if mem_ev:
                        evidence_items.append(mem_ev)
                except Exception as mem_err:
                    logger.warning(f"Memory evidence injection failed: {mem_err}")

            # Inject Knowledge Engine evidence (Task 9)
            from app.schemas.evidence import GovernmentSchemeEvidence, KnowledgeEvidence
            for doc in knowledge_docs:
                meta = doc.get("metadata", {})
                doc_id = doc.get("document_id") or meta.get("document_id", "doc-ref")
                title = doc.get("title") or meta.get("title", "Reference Library")
                category = doc.get("category") or meta.get("source_type") or "knowledge"

                if category == "government_scheme":
                    evidence_items.append(GovernmentSchemeEvidence(
                        id=f"EV-KE-{doc_id}",
                        source="KnowledgeEngine",
                        agent="KnowledgeEngine",
                        timestamp=time.time(),
                        confidence=doc.get("confidence", 0.9),
                        weight=1.0,
                        reasoning=doc.get("explanation", ""),
                        ontology_references=[doc_id],
                        metadata=meta,
                        scheme_title=title,
                        eligibility_matched=True
                    ))
                else:
                    evidence_items.append(KnowledgeEvidence(
                        id=f"EV-KE-{doc_id}",
                        source="KnowledgeEngine",
                        agent="KnowledgeEngine",
                        timestamp=time.time(),
                        confidence=doc.get("confidence", 0.9),
                        weight=1.0,
                        reasoning=doc.get("explanation", ""),
                        ontology_references=[doc_id],
                        metadata=meta,
                        citation=doc.get("citation", ""),
                        document_title=title
                    ))

            for agent_name, result in zip(active_called_agents, results, strict=True):
                if isinstance(result, BaseException):
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
             # Apply optimized confidence (Task 7)
            opt_confidence = self.learning_manager.confidence_optimizer.get_optimized_confidence(
                base_confidence=reasoning_result.overall_confidence,
                crop=crop,
                region=location
            )

            # Record knowledge feedback (Task 5 / Task 8)
            used_doc_ids = set()
            for ev in reasoning_result.evidence_used:
                if isinstance(ev, dict):
                    ev_id = ev.get("id")
                    if isinstance(ev_id, str) and ev_id.startswith("EV-KE-"):
                        used_doc_ids.add(ev_id[6:])
            for doc in knowledge_docs:
                meta = doc.get("metadata", {})
                doc_id = doc.get("document_id") or meta.get("document_id")
                if doc_id:
                    action = "cited" if doc_id in used_doc_ids else "ignored"
                    quality = meta.get("document_quality", 1.0)
                    if quality < 0.5:
                        try:
                            self.learning_manager.feedback_engine.record_knowledge_feedback(doc_id, "low_quality")
                        except Exception:
                            pass
                    try:
                        self.learning_manager.feedback_engine.record_knowledge_feedback(doc_id, action)
                    except Exception:
                        pass

            risk_score = reasoning_result.risk_assessment.risk_score if hasattr(reasoning_result.risk_assessment, "risk_score") else 0.0

            # 6. Response Validation (Task 6)
            rec_dict = self.builder.build_trusted_recommendation(
                summary=reasoning_result.summary,
                recommendation=reasoning_result.primary_recommendation,
                confidence=opt_confidence,
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

            # Auto-update twin after conversation (Task 6 / Task 8)
            if farmer_id:
                try:
                    self.twin_manager.update_twin_from_interaction(
                        farmer_id=farmer_id,
                        query=request.query,
                        response=reasoning_result.primary_recommendation
                    )
                except Exception as twin_up_err:
                    logger.warning(f"Twin auto-update from interaction failed: {twin_up_err}")

            # Run autonomous monitoring cycle after conversation updates (Sprint 15 Task 8)
            if farmer_id:
                try:
                    self.autonomous_manager.run_monitoring_cycle(farmer_id)
                except Exception as auto_err:
                    logger.warning(f"Autonomous cycle trigger failed: {auto_err}")

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
