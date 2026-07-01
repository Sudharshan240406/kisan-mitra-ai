import logging
import time
from typing import Any

from app.channels.envelope import ResponseEnvelope
from app.channels.envelope import LanguageMetadata, MessageEnvelope, MessagePriority
from app.media.events import MediaEventType
from app.media.media import MediaInput, MediaResult, MediaType
from app.multimodal.evidence import MultimodalEvidenceExtractor
from app.multimodal.validation import ImageValidationEngine, supports_image_validation
from app.schemas.responses import TrustedRecommendation
from app.utils.id import generate_uuid

logger = logging.getLogger("kisan_mitra_ai.media.pipeline")


class MediaPipeline:
    """
    Cognitive processing pipeline executing: Ingest -> Validate -> Extraction -> Policy Scan -> Route.
    """
    def __init__(self, container: Any) -> None:
        self._container = container
        self._registry = container.media_provider_registry
        self._session_manager = container.media_session_manager
        self._evidence_extractor = MultimodalEvidenceExtractor()
        self._image_validator = ImageValidationEngine()

    async def execute(self, media_input: MediaInput, conversation_id: str) -> dict[str, Any]:
        """
        Executes the Media Ingestion & Extraction pipeline:
        Validation -> Metadata Extraction -> Normalization -> Media Intelligence Extraction -> Policy Validation -> Routing.
        """
        start_time = time.perf_counter()
        trace_id = f"MIP-TR-{generate_uuid()[:8]}"
        session_id = conversation_id

        # Publish MediaReceived event
        self._publish_event(
            MediaEventType.MEDIA_RECEIVED.value,
            trace_id=trace_id,
            session_id=session_id,
            payload={
                "media_id": media_input.media_id,
                "filename": media_input.filename,
                "media_type": media_input.media_type.value
            }
        )

        # 1. Validation
        validation_errors = self._validate_media(media_input)
        if validation_errors:
            err_msg = f"Media Validation Failed: {', '.join(validation_errors)}"
            logger.warning(err_msg)
            self._publish_event(
                MediaEventType.MEDIA_REJECTED.value,
                trace_id=trace_id,
                session_id=session_id,
                payload={"media_id": media_input.media_id, "error": err_msg}
            )

            # Record telemetry
            if hasattr(self._container, "telemetry"):
                self._container.telemetry.record("media_validation_failure", 1, trace_id, session_id)

            return {"success": False, "status": "rejected", "errors": validation_errors}

        # Publish MediaValidated event
        self._publish_event(
            MediaEventType.MEDIA_VALIDATED.value,
            trace_id=trace_id,
            session_id=session_id,
            payload={"media_id": media_input.media_id}
        )

        # 2. Start Media Session
        media_session = self._session_manager.create_session(
            conversation_id=conversation_id,
            media_type=media_input.media_type.value
        )

        # Discover provider
        providers = self._registry.discover_by_type(media_input.media_type)
        if not providers:
            err_msg = f"No active provider found for media type '{media_input.media_type.value}'"
            self._session_manager.close_session(media_session.media_session_id)
            return {"success": False, "status": "failed", "error": err_msg}
        provider = providers[0]
        multimodal_session = self._container.multimodal_platform.start_session(
            session_id=media_session.media_session_id,
            media_type=media_input.media_type,
            provider_id=provider.id,
        )
        media_context = self._container.multimodal_platform.build_context(
            media_input=media_input,
            conversation_id=conversation_id,
            trace_id=trace_id,
        )

        # 3. Media Intelligence Extraction
        logger.info(f"Dispatching media processing to provider '{provider.id}'")
        try:
            media_result = await provider.process(media_input)
        except Exception as e:
            logger.error(f"Provider processing failed: {e}")
            self._publish_event(
                MediaEventType.PROCESSING_FAILED.value,
                trace_id=trace_id,
                session_id=session_id,
                payload={"media_id": media_input.media_id, "error": str(e)}
            )
            self._container.multimodal_platform.fail_session(media_session.media_session_id, str(e))
            self._session_manager.close_session(media_session.media_session_id)
            return {"success": False, "status": "failed", "error": str(e)}

        # 4. Policy & Governance checks on extracted text
        policy_passed = True
        policy_violations = []
        if media_result.extracted_text and hasattr(self._container, "policy_engine"):
            # Create a mock TrustedRecommendation to pass to the policy engine
            from app.core.context import AgentContext
            from app.schemas.responses import TrustedRecommendation

            rec = TrustedRecommendation(
                summary="Media transcription scan.",
                recommendation=media_result.extracted_text,
                confidence=media_result.confidence,
                risk=0.1,
                sources=["media_source"],
                safety_assessment={},
                reasoning_graph_ref="dummy_ref"
            )
            context = AgentContext(
                request_id=media_input.media_id,
                trace_id=trace_id,
                session_id=conversation_id,
                language="en"
            )

            reports = await self._container.policy_engine.evaluate(rec, context)
            for report in reports:
                if not report.passed:
                    policy_passed = False
                    policy_violations.extend(report.violations)

        if not policy_passed:
            err_msg = f"Policy violation detected in media text: {', '.join(policy_violations)}"
            logger.warning(err_msg)

            # Publish event
            self._publish_event(
                MediaEventType.MEDIA_REJECTED.value,
                trace_id=trace_id,
                session_id=session_id,
                payload={"media_id": media_input.media_id, "error": err_msg, "violations": policy_violations}
            )

            # Record telemetry
            if hasattr(self._container, "telemetry"):
                self._container.telemetry.record("media_policy_violation", 1, trace_id, session_id)

            self._session_manager.close_session(media_session.media_session_id)
            return {"success": False, "status": "rejected", "errors": policy_violations}

        # 5. Convert multimodal extraction into structured evidence and route through Reasoning Platform
        evidences = self._evidence_extractor.extract(media_result, media_context)
        logger.info("Routing multimodal evidence through ChiefReasoningAgent.")
        reasoning_result = await self._container.chief_agent.reason(
            query=media_result.extracted_text or media_input.filename,
            trace_id=trace_id,
            request_id=media_input.media_id,
            parsed_evidence=evidences,
            missing_fields=[field_name for field_name in ("crop", "location") if not any(ev.metadata.get(field_name) for ev in evidences)],
            language=media_context.language,
            crop=next((ev.metadata.get("crop") for ev in evidences if ev.metadata.get("crop")), None),
            location=next((ev.metadata.get("location") for ev in evidences if ev.metadata.get("location")), None),
        )
        trusted = TrustedRecommendation(
            summary=reasoning_result.summary,
            recommendation=reasoning_result.primary_recommendation,
            evidence=reasoning_result.evidence_used,
            confidence=reasoning_result.overall_confidence,
            risk=reasoning_result.risk_assessment.risk_score,
            reasoning=reasoning_result.reasoning_path,
            sources=list({ev.get("source", "") for ev in reasoning_result.evidence_used}),
            warnings=reasoning_result.warnings,
            missing_information=reasoning_result.missing_information,
            follow_up_required=reasoning_result.suggested_actions,
            safety_assessment={
                "consensus_reached": reasoning_result.consensus_reached,
                "conflicts_detected": reasoning_result.conflicts_detected,
                "escalated": reasoning_result.escalated,
                "explanation": reasoning_result.explanation,
                "calibration_flags": reasoning_result.calibration_flags,
                "confidence_interval": reasoning_result.confidence_interval,
                "multimodal": True,
                "media_type": media_input.media_type.value,
            },
            reasoning_graph_ref=reasoning_result.reasoning_graph_ref or reasoning_result.result_id,
        )
        response_envelope = ResponseEnvelope(
            message_id=media_input.media_id,
            conversation_id=conversation_id,
            channel="web-001",
            receiver="farmer-media",
            language=LanguageMetadata(preferred_language=media_context.language, locale=f"{media_context.language}-IN"),
            payload=trusted.model_dump(),
            trace_id=trace_id,
            status="success",
        )

        # Record Telemetry Metrics
        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
        if hasattr(self._container, "telemetry"):
            self._container.telemetry.record(
                "media_processing_latency_ms",
                latency_ms,
                trace_id=trace_id,
                session_id=session_id,
                metadata={"media_type": media_input.media_type.value, "provider": provider.id}
            )
        self._container.multimodal_telemetry.record_processing(
            media_type=media_input.media_type,
            trace_id=trace_id,
            session_id=session_id,
            latency_ms=latency_ms,
            confidence=reasoning_result.overall_confidence,
            provider_id=provider.id,
            reasoning_integrated=True,
        )
        self._container.multimodal_platform.complete_session(
            media_session.media_session_id,
            confidence=reasoning_result.overall_confidence,
            reasoning_ref=reasoning_result.reasoning_graph_ref,
            metadata={"provider_id": provider.id, "media_id": media_input.media_id},
        )

        # Publish final events
        self._publish_event(
            MediaEventType.MEDIA_PROCESSED.value,
            trace_id=trace_id,
            session_id=session_id,
            payload={"media_id": media_input.media_id}
        )
        self._publish_event(
            MediaEventType.PROCESSING_COMPLETED.value,
            trace_id=trace_id,
            session_id=session_id,
            payload={"media_id": media_input.media_id, "latency_ms": latency_ms}
        )

        self._session_manager.close_session(media_session.media_session_id)

        return {
            "success": True,
            "status": "completed",
            "media_result": media_result,
            "response": response_envelope,
            "reasoning_result": reasoning_result,
            "latency_ms": latency_ms
        }

    def _validate_media(self, media_input: MediaInput) -> list[str]:
        errors = []
        # Max file size 20MB
        max_size = 20 * 1024 * 1024
        if media_input.metadata.file_size_bytes > max_size:
            errors.append(f"File size exceeds maximum threshold of {max_size} bytes.")

        # Check supported formats
        supported_formats = {
            MediaType.VOICE: ["mp3", "wav", "m4a"],
            MediaType.IMAGE: ["png", "jpg", "jpeg", "tiff"],
            MediaType.DOCUMENT: ["pdf", "txt", "docx"],
            MediaType.SENSOR: ["csv", "json", "xml"],
            MediaType.DRONE_IMAGE: ["tif", "tiff", "geojson"],
            MediaType.VIDEO: ["mp4", "avi", "mkv"]
        }

        mtype = media_input.media_type
        fmt = media_input.metadata.format.lower().replace(".", "")
        if mtype in supported_formats:
            if fmt not in supported_formats[mtype]:
                errors.append(f"Format '.{fmt}' is not supported for media type '{mtype.value}'.")
        else:
            errors.append(f"Unsupported media type: '{mtype.value}'.")

        if supports_image_validation(media_input.media_type):
            report = self._image_validator.validate(media_input)
            errors.extend(report.errors)

        return errors

    def _publish_event(self, event_type: str, trace_id: str, session_id: str, payload: dict[str, Any]) -> None:
        if hasattr(self._container, "event_bus") and self._container.event_bus:
            try:
                from app.core.event_bus import Event
                self._container.event_bus.publish(Event(
                    event_type=event_type,
                    trace_id=trace_id,
                    request_id="media_pipeline",
                    session_id=session_id,
                    payload=payload
                ))
            except Exception as e:
                logger.error(f"Failed to publish MIP event '{event_type}': {e}")
