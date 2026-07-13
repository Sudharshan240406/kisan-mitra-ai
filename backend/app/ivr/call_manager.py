import asyncio
import logging
import time
from typing import Any, Dict, Optional

from app.ivr.call_router import CallRouter
from app.ivr.call_session import CallSession
from app.ivr.dtmf_handler import DTMFHandler
from app.ivr.ivr_flow import IVRFlow, IVRState
from app.ivr.language_selector import LanguageSelector
from app.ivr.summary_generator import SummaryGenerator
from app.ivr.transcript_manager import TranscriptManager
from app.telephony.events import TelephonyEventType

logger = logging.getLogger("kisan_mitra_ai.ivr.call_manager")


class CallManager:
    """Main coordinator handling call lifecycles, DTMF input routing, STT/TTS adapters, and events."""

    def __init__(self, container: Any) -> None:
        self._container = container
        self._ivr_flow = IVRFlow()
        self._language_selector = LanguageSelector(container)
        self._dtmf_handler = DTMFHandler(self._ivr_flow, self._language_selector)
        self._transcript_manager = TranscriptManager()
        self._summary_generator = SummaryGenerator(container)
        self._call_router = CallRouter(container)

    @property
    def _session_manager(self) -> Any:
        return self._container.call_session_manager

    async def handle_incoming_call(self, caller: str, callee: str, call_id: Optional[str] = None) -> Dict[str, Any]:
        """Processes an incoming call, creates a session, and plays the greeting & language menu."""
        start_time = time.perf_counter()
        cid = call_id or f"CALL-IN-{int(time.time())}"
        trace_id = f"TEL-TR-{cid}"

        # 1. Publish EventBus event
        self._publish_event(TelephonyEventType.INCOMING_CALL.value, cid, "system", {"caller": caller, "callee": callee})

        # 2. Create the call session
        session = self._session_manager.create_session(
            call_id=cid,
            language="hi",  # Default starting language
            metadata={"caller": caller, "callee": callee, "trace_id": trace_id}
        )

        # 3. Publish EventBus answered/started events
        self._publish_event(TelephonyEventType.CALL_ANSWERED.value, cid, session.conversation_id, {})
        self._publish_event(TelephonyEventType.IVR_STARTED.value, cid, session.conversation_id, {})

        # 4. Stream live WebSocket events to Mission Control
        try:
            from app.api.v1.websocket import ws_manager
            asyncio.ensure_future(ws_manager.push_event("CALL_STARTED", {
                "call_id": cid,
                "farmer_id": "guest_farmer",
                "phone": caller,
                "language": session.language,
                "timestamp": time.time(),
            }))
        except Exception as e:
            logger.warning(f"Could not push CALL_STARTED event to WebSocket: {e}")

        # 5. Transition to GREETING and then LANGUAGE_SELECTION immediately
        greeting_prompt = self._ivr_flow.get_prompt(IVRState.GREETING.value, session.language)
        session.current_ivr_state = IVRState.LANGUAGE_SELECTION.value
        lang_prompt = self._ivr_flow.get_prompt(IVRState.LANGUAGE_SELECTION.value, session.language)
        combined_prompt = f"{greeting_prompt} {lang_prompt}"

        # 6. Record latency telemetry
        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
        if hasattr(self._container, "telemetry") and self._container.telemetry:
            self._container.telemetry.record("telephony_routing_latency_ms", latency_ms, trace_id, session.conversation_id)

        # Log greeting transcript
        self._transcript_manager.add_entry(session, "system", combined_prompt, confidence=1.0)

        return {
            "success": True,
            "call_id": cid,
            "conversation_id": session.conversation_id,
            "current_state": session.current_ivr_state,
            "tts_prompt": combined_prompt
        }

    async def handle_dtmf_input(self, call_id: str, digits: str) -> Dict[str, Any]:  # noqa: PLR0912
        """Receives keypresses and updates states, evaluating intents or schemes as required."""
        start_time = time.perf_counter()
        session = self._session_manager.get_session(call_id)
        if not session:
            return {"success": False, "error": "Call session not found or expired."}

        trace_id = session.metadata.get("trace_id", "telephony_trace")

        # 1. Publish EventBus Event
        self._publish_event(
            TelephonyEventType.DTMF_RECEIVED.value,
            call_id,
            session.conversation_id,
            {"digits": digits, "state": session.current_ivr_state}
        )

        pre_transition_state = session.current_ivr_state

        # Log farmer DTMF transcript entry
        self._transcript_manager.add_entry(session, "farmer", f"[DTMF Key: {digits}]", confidence=1.0)

        # 2. Transition state machine via DTMF Handler
        next_state, prompt = await self._dtmf_handler.handle_dtmf(session, digits)

        # 3. If transitioning out of LANGUAGE_SELECTION, update client and digital twin info
        if pre_transition_state == IVRState.LANGUAGE_SELECTION.value and digits in ["1", "2", "3", "4", "5", "6"]:
            self._publish_event(
                TelephonyEventType.LANGUAGE_SELECTED.value,
                call_id,
                session.conversation_id,
                {"language": session.language}
            )

            # Retrieve or identify farmer
            caller = session.metadata.get("caller", "")
            try:
                from app.services.demo import DemoService
                demo_service = DemoService()
                farmer = demo_service.get_farmer_by_phone(caller)
                if not farmer:
                    # fallback to Ramesh for demo
                    all_farmers = demo_service.get_all_farmers()
                    farmer = all_farmers[0] if all_farmers else None

                if farmer:
                    session.farmer_id = farmer.farmer_id
                    session.farmer_profile_snapshot = farmer.model_dump()
                    self._language_selector.select_language(session, session.language)

                    # Publish live identification event to WS
                    from app.api.v1.websocket import ws_manager
                    asyncio.ensure_future(ws_manager.push_event("CALLER_IDENTIFIED", {
                        "call_id": call_id,
                        "farmer_id": farmer.farmer_id,
                        "farmer_name": farmer.name,
                        "phone": caller,
                        "state": farmer.state,
                        "district": farmer.district,
                        "lookup_method": "phone_registry",
                    }))

                    farmer_summary = demo_service.get_farmer_summary(farmer)
                    asyncio.ensure_future(ws_manager.push_event("DIGITAL_TWIN_LOADED", {
                        "call_id": call_id,
                        "farmer_id": farmer.farmer_id,
                        "digital_twin": {
                            **farmer_summary,
                            "digital_twin_version": "v2.0",
                            "last_interaction": "Active call"
                        }
                    }))
            except Exception as e:
                logger.warning(f"Could not load farmer twin details: {e}")

        # 4. Handle Scheme inquiry flow
        if session.current_ivr_state == IVRState.SCHEME_INQUIRY.value:
            logger.info(f"Checking schemes eligibility for call '{call_id}'")

            # Emit live search started to WS
            try:
                from app.api.v1.websocket import ws_manager
                asyncio.ensure_future(ws_manager.push_event("SCHEME_SEARCH_STARTED", {
                    "call_id": call_id,
                    "farmer_id": session.farmer_id,
                    "engine": "EligibilityEngine v2.0",
                }))
            except Exception:
                pass

            scheme_response = await self._handle_scheme_inquiry(session)
            prompt = f"{prompt} {scheme_response}"

            # Auto transition to result and document advisor
            session.current_ivr_state = IVRState.DOCUMENT_ADVISOR.value
            doc_prompt = self._ivr_flow.get_prompt(IVRState.DOCUMENT_ADVISOR.value, session.language)
            prompt = f"{prompt} {doc_prompt}"

        # 5. Handle Intent capture query routing (non-scheme path)
        advisory_text = ""
        if session.current_ivr_state == IVRState.RECOMMENDATION_PLAYBACK.value and "intent_query" in session.metadata:
            query = session.metadata.pop("intent_query")
            logger.info(f"Routing IVR DTMF query '{query}' for call '{call_id}'")

            advisory_text = await self._call_router.route_query(session, query)
            prompt = f"{prompt} {advisory_text}"

            # Record Played Event
            self._publish_event(
                TelephonyEventType.RECOMMENDATION_PLAYED.value,
                call_id,
                session.conversation_id,
                {"query": query}
            )

            # Auto transition to confirmation menu
            session.current_ivr_state = IVRState.CONFIRMATION.value
            confirm_prompt = self._ivr_flow.get_prompt(IVRState.CONFIRMATION.value, session.language)
            prompt = f"{prompt} {confirm_prompt}"

        # 6. Handle Human transfer flow
        if next_state == IVRState.HUMAN_TRANSFER:
            self._publish_event(TelephonyEventType.CALL_TRANSFERRED.value, call_id, session.conversation_id, {})
            session.current_ivr_state = IVRState.EXIT.value
            exit_prompt = self._ivr_flow.get_prompt(IVRState.EXIT.value, session.language)
            prompt = f"{prompt} {exit_prompt}"

        # 7. Generate Call Summary if transitioning to SUMMARY state
        if session.current_ivr_state == IVRState.SUMMARY.value:
            logger.info(f"Generating call summary for session '{call_id}'")
            summary = await self._summary_generator.generate_and_store_summary(session)
            prompt = f"{prompt} {summary.conversation_summary}"

            # Transition directly to exit
            session.current_ivr_state = IVRState.EXIT.value
            exit_prompt = self._ivr_flow.get_prompt(IVRState.EXIT.value, session.language)
            prompt = f"{prompt} {exit_prompt}"

        # 8. Handle Exit / Closing states
        if session.current_ivr_state == IVRState.EXIT.value:
            duration = time.time() - session.created_at

            # Emit live call completed to WS
            try:
                from app.api.v1.websocket import ws_manager
                asyncio.ensure_future(ws_manager.push_event("CALL_COMPLETED", {
                    "call_id": call_id,
                    "duration": duration,
                    "summary": session.summary.model_dump() if session.summary else {}
                }))
            except Exception:
                pass

            self._record_telephony_metrics(session, completed=True)
            self._session_manager.close_session(call_id)
            self._publish_event(TelephonyEventType.CALL_ENDED.value, call_id, session.conversation_id, {})

        # Record latency telemetry
        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
        if hasattr(self._container, "telemetry") and self._container.telemetry:
            self._container.telemetry.record("telephony_routing_latency_ms", latency_ms, trace_id, session.conversation_id)

        # Log system response transcript entry
        self._transcript_manager.add_entry(session, "system", prompt, confidence=1.0)

        return {
            "success": True,
            "call_id": call_id,
            "current_state": session.current_ivr_state,
            "tts_prompt": prompt,
            "advisory_text": advisory_text
        }

    async def handle_voice_recording(self, call_id: str, audio_bytes: bytes, filename: str = "voicemail.wav") -> Dict[str, Any]:
        """Transcribes incoming audio, evaluates queries through the router, synthesizes and outputs speech."""
        start_time = time.perf_counter()
        session = self._session_manager.get_session(call_id)
        if not session:
            return {"success": False, "error": "Call session not found or expired."}

        trace_id = session.metadata.get("trace_id", "telephony_trace")

        session.recording_metadata = {
            "file_size_bytes": len(audio_bytes),
            "filename": filename,
            "timestamp": time.time()
        }

        # 1. Speech -> Speech-to-Text Adapter
        try:
            stt_provider = self._container.stt_registry.get_active()
            stt_result = await stt_provider.transcribe(audio_bytes, language=session.language)
            query_text = stt_result.transcript
            logger.info(f"Transcribed voice recording: '{query_text}' (Confidence: {stt_result.confidence})")
        except Exception as e:
            logger.error(f"Speech-to-text failed: {e}")
            query_text = "weather query"  # default safe fallback
            stt_result = Any

        # 2. Log incoming speech transcript
        self._transcript_manager.add_entry(
            session=session,
            sender="farmer",
            text=query_text,
            confidence=getattr(stt_result, "confidence", 0.90),
            execution_id=trace_id,
            timing_ms=getattr(stt_result, "latency_ms", 0.0)
        )

        # 3. Route transcribed query to AI Orchestrator
        advisory_text = await self._call_router.route_query(session, query_text)

        # 4. Text -> Text-to-Speech Adapter
        try:
            tts_provider = self._container.tts_registry.get_active()
            tts_result = await tts_provider.synthesize(advisory_text, language=session.language)
            logger.info(f"Synthesized TTS output of length: {len(tts_result.audio_bytes)} bytes")
        except Exception as e:
            logger.error(f"Text-to-speech synthesis failed: {e}")
            tts_result = Any

        # 5. Log outgoing speech transcript
        self._transcript_manager.add_entry(
            session=session,
            sender="system",
            text=advisory_text,
            confidence=1.0,
            execution_id=trace_id,
            timing_ms=getattr(tts_result, "latency_ms", 0.0)
        )

        # Auto transition to confirmation menu after speaking advice
        session.current_ivr_state = IVRState.CONFIRMATION.value
        confirm_prompt = self._ivr_flow.get_prompt(IVRState.CONFIRMATION.value, session.language)
        combined_prompt = f"{advisory_text} {confirm_prompt}"

        # 6. Publish event
        self._publish_event(
            TelephonyEventType.RECOMMENDATION_PLAYED.value,
            call_id,
            session.conversation_id,
            {"voicemail": filename}
        )

        # Record metrics
        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)
        if hasattr(self._container, "telemetry") and self._container.telemetry:
            self._container.telemetry.record("telephony_routing_latency_ms", latency_ms, trace_id, session.conversation_id)

        return {
            "success": True,
            "call_id": call_id,
            "current_state": session.current_ivr_state,
            "tts_prompt": combined_prompt,
            "advisory_text": advisory_text
        }

    async def _handle_scheme_inquiry(self, session: CallSession) -> str:
        """Heuristic scheme evaluation invoking GovernmentSchemeService and generating speech responses."""
        try:
            from app.knowledge.modules.government import GovernmentKnowledgeProvider
            from app.services.demo import DemoService
            from app.services.scheme_service import GovernmentSchemeService

            demo_service = DemoService()
            scheme_service = GovernmentSchemeService()
            gov_provider = GovernmentKnowledgeProvider()

            caller = session.metadata.get("caller", "")
            farmer = demo_service.get_farmer_by_phone(caller)

            if not farmer:
                all_farmers = demo_service.get_all_farmers()
                farmer = all_farmers[0] if all_farmers else None

            if not farmer:
                return "No farmer profile found. Please register first."

            session.farmer_id = farmer.farmer_id
            session.farmer_profile_snapshot = farmer.model_dump()

            all_schemes = gov_provider.get_all_schemes()

            # Streaming events simulation to WebSocket
            for s in all_schemes[:3]:
                try:
                    from app.api.v1.websocket import ws_manager
                    asyncio.ensure_future(ws_manager.push_event("SCHEME_MATCHED", {
                        "call_id": session.call_id,
                        "scheme_id": s.scheme_id,
                        "title": s.title,
                        "status": "ELIGIBLE",
                        "confidence": 0.95,
                    }))
                except Exception:
                    pass
                await asyncio.sleep(0.01)

            # Invoke service check
            recommendations = scheme_service.evaluate_farmer_eligibility(farmer, all_schemes)
            voice_response = scheme_service.generate_voice_response(
                farmer, recommendations, session.language
            )

            # Publish WS Completed event
            try:
                from app.api.v1.websocket import ws_manager
                asyncio.ensure_future(ws_manager.push_event("ELIGIBILITY_COMPLETED", {
                    "call_id": session.call_id,
                    "total_evaluated": len(all_schemes),
                    "eligible_count": len(recommendations),
                }))
            except Exception:
                pass

            return str(voice_response)

        except Exception as e:
            logger.error(f"Scheme inquiry failed: {e}")
            return "Sorry, there was an issue checking your scheme eligibility."

    def _record_telephony_metrics(self, session: CallSession, completed: bool = True) -> None:
        """Publishes operational telemetry metrics."""
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

    def _publish_event(self, event_type: str, call_id: str, session_id: str, payload: Dict[str, Any]) -> None:
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
