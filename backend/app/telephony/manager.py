import logging
import time
from typing import Any, Optional

from app.channels.envelope import LanguageMetadata, MessageEnvelope, MessagePriority
from app.media.media import MediaInput, MediaMetadata, MediaType
from app.telephony.events import TelephonyEventType
from app.telephony.ivr import IVRState
from app.telephony.sessions import CallSession
from app.utils.id import generate_uuid

logger = logging.getLogger("kisan_mitra_ai.telephony.manager")


class CallManager:
    """
    Coordinator managing incoming call endpoints, audio playback,
    voicemail pipelines, DTMF routing loops, EventBus and Telemetry metrics.
    """
    def __init__(self, container: Any) -> None:
        self._container = container
        self._registry = container.telephony_provider_registry
        self._session_manager = container.call_session_manager
        self._ivr_state_machine = container.ivr_state_machine

    async def handle_incoming_call(self, caller: str, callee: str, call_id: Optional[str] = None) -> dict[str, Any]:
        """
        Processes inbound call alert, starts session, publishes start events,
        and returns greeting TTS instructions.
        """
        start_time = time.perf_counter()
        cid = call_id or f"CALL-IN-{generate_uuid()[:8]}"
        trace_id = f"TEL-TR-{generate_uuid()[:8]}"

        # Publish IncomingCall
        self._publish_event(TelephonyEventType.INCOMING_CALL.value, cid, "system", {"caller": caller, "callee": callee})

        # Create call session
        session = self._session_manager.create_session(
            call_id=cid,
            language="hi",  # default
            metadata={"caller": caller, "callee": callee, "trace_id": trace_id}
        )

        # Publish CallAnswered
        self._publish_event(TelephonyEventType.CALL_ANSWERED.value, cid, session.conversation_id, {})
        # Publish IVRStarted
        self._publish_event(TelephonyEventType.IVR_STARTED.value, cid, session.conversation_id, {})

        # Transition to initial greeting
        prompt = await self._ivr_state_machine.get_prompt(IVRState.GREETING.value, session.language)

        # Transition immediately to LANGUAGE_SELECTION so we're ready for DTMF input
        _, lang_prompt = await self._ivr_state_machine.transition(session, "next")
        combined_prompt = f"{prompt} {lang_prompt}"

        # Record routing latency
        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
        if hasattr(self._container, "telemetry"):
            self._container.telemetry.record("telephony_routing_latency_ms", latency_ms, trace_id, session.conversation_id)

        return {
            "success": True,
            "call_id": cid,
            "conversation_id": session.conversation_id,
            "current_state": session.current_ivr_state,
            "tts_prompt": combined_prompt
        }

    async def handle_dtmf_input(self, call_id: str, digits: str) -> dict[str, Any]:
        """
        Receives DTMF digits, updates session language/state, processes intent,
        calls core agent query routing, and returns the response TTS instructions.
        """
        start_time = time.perf_counter()
        session = self._session_manager.get_session(call_id)
        if not session:
            return {"success": False, "error": "Call session not found or expired."}

        trace_id = session.metadata.get("trace_id", "telephony_trace")

        # Publish DTMFReceived event
        self._publish_event(
            TelephonyEventType.DTMF_RECEIVED.value,
            call_id,
            session.conversation_id,
            {"digits": digits, "state": session.current_ivr_state}
        )

        # Capture state before transition to check for specific flows
        pre_transition_state = session.current_ivr_state

        # Handle in state machine
        next_state, prompt = await self._ivr_state_machine.handle_dtmf(session, digits)

        # Check if language selected (fires when coming from LANGUAGE_SELECTION)
        if pre_transition_state == IVRState.LANGUAGE_SELECTION.value and digits in ["1", "2", "3"]:
            self._publish_event(
                TelephonyEventType.LANGUAGE_SELECTED.value,
                call_id,
                session.conversation_id,
                {"language": session.language}
            )

        # Handle Scheme Inquiry — eligibility evaluation flow
        if session.current_ivr_state == IVRState.SCHEME_INQUIRY.value:
            logger.info(f"Scheme inquiry triggered for call '{call_id}'")
            scheme_response = await self._handle_scheme_inquiry(session)
            prompt = f"{prompt} {scheme_response}"
            # Transition to SCHEME_RESULT then DOCUMENT_ADVISOR
            session.current_ivr_state = IVRState.DOCUMENT_ADVISOR.value
            doc_prompt = await self._ivr_state_machine.get_prompt(IVRState.DOCUMENT_ADVISOR.value, session.language)
            prompt = f"{prompt} {doc_prompt}"

        # Route query if INTENT triggered (non-scheme paths)
        advisory_text = ""
        if session.current_ivr_state == IVRState.RECOMMENDATION_PLAYBACK.value and "intent_query" in session.metadata:
            query = session.metadata.pop("intent_query")
            logger.info(f"Routing IVR intent query '{query}' for call '{call_id}'")

            # Route through omnichannel Core
            lang_metadata = LanguageMetadata(preferred_language=session.language, locale=session.language)
            envelope = MessageEnvelope(
                conversation_id=session.conversation_id,
                channel="ivr-001",  # IVR Channel ID
                sender=session.metadata.get("caller", "farmer-telephony"),
                receiver="system",
                language=lang_metadata,
                payload={"text": query},
                priority=MessagePriority.HIGH,
                trace_id=trace_id
            )

            try:
                response = await self._container.channel_router.route_inbound(envelope, asynchronous=False)
                if response and response.payload:
                    advisory_text = response.payload.get("recommendation") or response.payload.get("text") or ""
                else:
                    advisory_text = "Sorry, I could not generate a recommendation at this moment."
            except Exception as e:
                logger.error(f"Failed to query advisory: {e}")
                advisory_text = "An error occurred while generating your recommendation."

            prompt = f"{prompt} {advisory_text}"

            # Record Played event
            self._publish_event(
                TelephonyEventType.RECOMMENDATION_PLAYED.value,
                call_id,
                session.conversation_id,
                {"query": query}
            )

            # Auto transition to confirmation menu after speaking advice
            session.current_ivr_state = IVRState.CONFIRMATION.value
            confirm_prompt = await self._ivr_state_machine.get_prompt(IVRState.CONFIRMATION.value, session.language)
            prompt = f"{prompt} {confirm_prompt}"

        # If human transfer
        if next_state == IVRState.HUMAN_TRANSFER:
            self._publish_event(TelephonyEventType.CALL_TRANSFERRED.value, call_id, session.conversation_id, {})
            # Auto transition to exit
            session.current_ivr_state = IVRState.EXIT.value
            exit_prompt = await self._ivr_state_machine.get_prompt(IVRState.EXIT.value, session.language)
            prompt = f"{prompt} {exit_prompt}"

        # If exit/closed
        if session.current_ivr_state == IVRState.EXIT.value:
            # Touch metrics before cleanup
            self._record_telephony_metrics(session, completed=True)
            self._session_manager.close_session(call_id)
            self._publish_event(TelephonyEventType.CALL_ENDED.value, call_id, session.conversation_id, {})

        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
        if hasattr(self._container, "telemetry"):
            self._container.telemetry.record("telephony_routing_latency_ms", latency_ms, trace_id, session.conversation_id)

        return {
            "success": True,
            "call_id": call_id,
            "current_state": session.current_ivr_state,
            "tts_prompt": prompt,
            "advisory_text": advisory_text
        }

    async def handle_voice_recording(self, call_id: str, audio_bytes: bytes, filename: str = "voicemail.wav") -> dict[str, Any]:
        """
        Receives call voicemail audio bytes, processes them via MediaPipeline transcription,
        resolves queries, and returns TTS prompt playback responses.
        """
        start_time = time.perf_counter()
        session = self._session_manager.get_session(call_id)
        if not session:
            return {"success": False, "error": "Call session not found or expired."}

        trace_id = session.metadata.get("trace_id", "telephony_trace")

        # Start recording trace
        session.recording_metadata = {
            "file_size_bytes": len(audio_bytes),
            "filename": filename,
            "timestamp": time.time()
        }

        # Build media pipeline input
        fmt = filename.rsplit(".", maxsplit=1)[-1] if "." in filename else "wav"
        media_input = MediaInput(
            media_type=MediaType.VOICE,
            filename=filename,
            content=audio_bytes,
            metadata=MediaMetadata(file_size_bytes=len(audio_bytes), format=fmt)
        )

        logger.info(f"Processing call voice recording '{filename}' through Media Pipeline...")

        # Execute pipeline
        result = await self._container.media_pipeline.execute(media_input, session.conversation_id)

        # Check result
        if not result.get("success", False):
            # Rejected or failed
            errs = result.get("errors", [result.get("error", "Unknown error")])
            err_msg = ", ".join(errs) if isinstance(errs, list) else str(errs)

            prompt = f"Sorry, processing failed. {err_msg}"
            session.current_ivr_state = IVRState.CONFIRMATION.value
            confirm_prompt = await self._ivr_state_machine.get_prompt(IVRState.CONFIRMATION.value, session.language)

            if hasattr(self._container, "telemetry"):
                self._container.telemetry.record("telephony_error_count", 1, trace_id, session.conversation_id)

            return {
                "success": False,
                "call_id": call_id,
                "current_state": session.current_ivr_state,
                "tts_prompt": f"{prompt} {confirm_prompt}",
                "error": err_msg
            }

        # Successful routing
        response_env = result["response"]
        advisory_text = ""
        if response_env and response_env.payload:
            advisory_text = response_env.payload.get("recommendation") or response_env.payload.get("text") or ""

        # Speak advisory
        playback_prompt = await self._ivr_state_machine.get_prompt(IVRState.RECOMMENDATION_PLAYBACK.value, session.language)
        combined_prompt = f"{playback_prompt} {advisory_text}"

        # Record played event
        self._publish_event(
            TelephonyEventType.RECOMMENDATION_PLAYED.value,
            call_id,
            session.conversation_id,
            {"voicemail": filename}
        )

        # Auto transition to confirmation menu
        session.current_ivr_state = IVRState.CONFIRMATION.value
        confirm_prompt = await self._ivr_state_machine.get_prompt(IVRState.CONFIRMATION.value, session.language)
        combined_prompt = f"{combined_prompt} {confirm_prompt}"

        # Record call metrics
        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
        if hasattr(self._container, "telemetry"):
            self._container.telemetry.record("telephony_routing_latency_ms", latency_ms, trace_id, session.conversation_id)

        return {
            "success": True,
            "call_id": call_id,
            "current_state": session.current_ivr_state,
            "tts_prompt": combined_prompt,
            "advisory_text": advisory_text
        }

    async def _handle_scheme_inquiry(self, session: CallSession) -> str:
        """
        Handle government scheme inquiry: identify farmer, evaluate eligibility,
        generate natural voice response.
        """
        try:
            from app.knowledge.modules.government import GovernmentKnowledgeProvider
            from app.services.demo import DemoService
            from app.services.eligibility import EligibilityEngine
            from app.services.scheme_service import GovernmentSchemeService

            demo_service = DemoService()
            scheme_service = GovernmentSchemeService()
            gov_provider = GovernmentKnowledgeProvider()

            # Try to identify farmer by caller number
            caller = session.metadata.get("caller", "")
            farmer = demo_service.get_farmer_by_phone(caller)

            if not farmer:
                # Use first demo farmer as fallback for demo
                all_farmers = demo_service.get_all_farmers()
                farmer = all_farmers[0] if all_farmers else None

            if not farmer:
                return "No farmer profile found. Please register first."

            # Bind farmer to session
            session.farmer_id = farmer.farmer_id
            session.farmer_profile_snapshot = farmer.model_dump()

            # Evaluate all schemes
            all_schemes = gov_provider.get_all_schemes()
            recommendations = scheme_service.evaluate_farmer_eligibility(farmer, all_schemes)

            # Generate natural voice response
            voice_response = scheme_service.generate_voice_response(
                farmer, recommendations, session.language
            )

            return voice_response

        except Exception as e:
            logger.error(f"Scheme inquiry failed: {e}")
            return "Sorry, there was an issue checking your scheme eligibility. Please try again."

    def _record_telephony_metrics(self, session: CallSession, completed: bool = True) -> None:
        """Publishes operational telemetry metrics to Telemetry Framework."""
        if not hasattr(self._container, "telemetry") or not self._container.telemetry:
            return

        duration = time.time() - session.created_at
        trace_id = session.metadata.get("trace_id", "telephony_trace")

        self._container.telemetry.record(
            "telephony_call_duration_seconds",
            duration,
            trace_id=trace_id,
            session_id=session.conversation_id,
            metadata={"language": session.language, "completed": completed}
        )
        self._container.telemetry.record(
            "telephony_ivr_completion",
            1.0 if completed else 0.0,
            trace_id=trace_id,
            session_id=session.conversation_id
        )
        self._container.telemetry.record(
            "telephony_retry_count",
            session.recovery_count,
            trace_id=trace_id,
            session_id=session.conversation_id
        )

    def _publish_event(self, event_type: str, call_id: str, session_id: str, payload: dict[str, Any]) -> None:
        if hasattr(self._container, "event_bus") and self._container.event_bus:
            try:
                from app.core.event_bus import Event
                self._container.event_bus.publish(Event(
                    event_type=event_type,
                    trace_id=f"call_{call_id}",
                    request_id="call_manager",
                    session_id=session_id,
                    payload=payload
                ))
            except Exception as e:
                logger.error(f"Failed to publish call event '{event_type}': {e}")
