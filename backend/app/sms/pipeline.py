import logging
import re
import time
from collections import defaultdict
from typing import Any, Optional, cast

from app.channels.envelope import LanguageMetadata, MessageEnvelope, MessagePriority
from app.sms.events import SMSEventType
from app.utils.id import generate_uuid

logger = logging.getLogger("kisan_mitra_ai.sms.pipeline")


class SMSRateLimiter:
    """
    In-memory rate limiter tracking query frequencies and duplications per caller number.
    """
    def __init__(self, max_requests: int = 5, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_message: dict[str, tuple[str, float]] = {}

    def is_spam(self, phone: str, text: str) -> Optional[str]:
        now = time.time()

        # 1. Duplication check within 5 seconds
        last = self._last_message.get(phone)
        if last:
            last_text, last_time = last
            if last_text == text and (now - last_time) < 5.0:
                return "Duplicate message within 5 seconds."
        self._last_message[phone] = (text, now)

        # 2. Rate limit count check
        history = self._history[phone]
        history[:] = [t for t in history if (now - t) < self.window_seconds]
        if len(history) >= self.max_requests:
            return f"Rate limit exceeded: max {self.max_requests} messages per minute."

        history.append(now)
        return None


class SMSPipeline:
    """
    SMS Message Pipeline: Validate -> Ingest Session -> Policy Scan -> Route Graph -> Template Render -> Deliver.
    """
    def __init__(self, container: Any) -> None:
        self._container = container
        self._registry = container.sms_provider_registry
        self._session_manager = container.sms_session_manager
        self._template_engine = container.sms_template_engine
        self._rate_limiter = SMSRateLimiter()

    async def execute(self, sender_phone: str, message_body: str, recipient_phone: str = "kisan_mitra") -> dict[str, Any]:
        """
        Runs the SMS pipeline, resolves multi-agent advice, and sends dynamic replies.
        """
        start_time = time.perf_counter()
        trace_id = f"SMS-TR-{generate_uuid()[:8]}"

        self._publish_event(
            SMSEventType.SMS_RECEIVED.value,
            trace_id,
            "session-new",
            {"sender": sender_phone, "body": message_body}
        )

        # 1. Validation
        validation_fail = self._handle_validation(sender_phone, message_body, trace_id)
        if validation_fail:
            return validation_fail

        # 2. Retrieve or Create Session
        session = self._get_or_create_session(sender_phone, trace_id)
        session.thread_history.append({"direction": "inbound", "text": message_body, "timestamp": time.time()})

        # 3. Policy scanning
        policy_fail = await self._handle_policy_scan(message_body, trace_id, session)
        if policy_fail:
            return policy_fail

        # 4. Routing
        advisory_text, template_key = await self._route_and_classify(message_body, sender_phone, session, trace_id)

        # 5. Render template
        rendered_reply = self._render_response(advisory_text, template_key, session, trace_id)

        # 6. Outbox delivery
        return await self._deliver_outbound(sender_phone, rendered_reply, session, trace_id, start_time)

    def _handle_validation(self, sender_phone: str, message_body: str, trace_id: str) -> Optional[dict[str, Any]]:
        validation_errors = self._validate_message(sender_phone, message_body)
        if not validation_errors:
            return None

        err_msg = f"SMS Inbound Validation Failed: {', '.join(validation_errors)}"
        logger.warning(err_msg)
        self._publish_event(
            SMSEventType.SMS_FAILED.value,
            trace_id,
            "session-fail",
            {"error": err_msg}
        )
        if hasattr(self._container, "telemetry"):
            self._container.telemetry.record("sms_validation_failure", 1, trace_id, "session-fail")
        return {"success": False, "status": "rejected", "errors": validation_errors}

    def _get_or_create_session(self, sender_phone: str, trace_id: str) -> Any:
        session = self._session_manager.get_session_by_phone(sender_phone)
        if not session:
            session = self._session_manager.create_session(
                phone_number=sender_phone,
                language="hi"
            )
        else:
            session.touch()

        if hasattr(self._container, "telemetry"):
            self._container.telemetry.record(
                "sms_session_language",
                1,
                trace_id,
                session.conversation_id,
                metadata={"language": session.language}
            )
        return session

    async def _handle_policy_scan(self, message_body: str, trace_id: str, session: Any) -> Optional[dict[str, Any]]:
        policy_passed = True
        policy_violations = []
        if hasattr(self._container, "policy_engine"):
            from app.core.context import AgentContext
            from app.schemas.responses import TrustedRecommendation

            rec = TrustedRecommendation(
                summary="SMS input scan.",
                recommendation=message_body,
                confidence=1.0,
                risk=0.1,
                sources=["sms_source"],
                safety_assessment={},
                reasoning_graph_ref="dummy_ref"
            )
            context = AgentContext(
                request_id=f"SMS-RQ-{generate_uuid()[:8]}",
                trace_id=trace_id,
                session_id=session.conversation_id,
                language=session.language
            )
            reports = await self._container.policy_engine.evaluate(rec, context)
            for report in reports:
                if not report.passed:
                    policy_passed = False
                    policy_violations.extend(report.violations)

        if not policy_passed:
            err_msg = f"Policy violation detected in SMS body: {', '.join(policy_violations)}"
            logger.warning(err_msg)
            self._publish_event(
                SMSEventType.SMS_FAILED.value,
                trace_id,
                session.conversation_id,
                {"error": err_msg}
            )
            if hasattr(self._container, "telemetry"):
                self._container.telemetry.record("sms_policy_violation", 1, trace_id, session.conversation_id)
            self._session_manager.close_session(session.sms_session_id)
            return {"success": False, "status": "rejected", "errors": policy_violations}

        return None

    async def _route_and_classify(self, message_body: str, sender_phone: str, session: Any, trace_id: str) -> tuple[str, str]:
        logger.info(f"Routing SMS query to Omnichannel: {message_body[:30]}")
        lang_metadata = LanguageMetadata(preferred_language=session.language, locale=session.language)
        envelope = MessageEnvelope(
            conversation_id=session.conversation_id,
            channel="sms-01",
            sender=sender_phone,
            receiver="system",
            language=lang_metadata,
            payload={"text": message_body},
            priority=MessagePriority.NORMAL,
            trace_id=trace_id
        )

        advisory_text = ""
        template_key = "general"
        try:
            response = await self._container.channel_router.route_inbound(envelope, asynchronous=False)
            if response and response.payload:
                advisory_text = response.payload.get("recommendation") or response.payload.get("text") or ""
                tags = response.payload.get("classification_tags", [])
                template_key = self._determine_template(message_body, tags)
            else:
                advisory_text = "Sorry, we could not generate a crop advisory at this moment."
        except Exception as e:
            logger.error(f"SMS pipeline graph routing failed: {e}")
            advisory_text = "An error occurred while generating crop advice."

        return advisory_text, template_key

    def _render_response(self, advisory_text: str, template_key: str, session: Any, trace_id: str) -> str:
        render_kwargs = {
            "farmer_name": "Farmer",
            "scheme_name": "Kisan Credit Card",
            "details": "Easy credit limits",
            "region": "Punjab",
            "weather_condition": "Clear Sky",
            "temp": "28",
            "crop_name": "Wheat",
            "market": "Khanna",
            "price": "2400",
            "disease": "Yellow Rust",
            "recommendation": "Spray fungicide",
            "otp_code": "4892",
            "advisor_name": "Dr. Sharma",
            "date": "Tomorrow",
            "time": "10:00 AM",
            "advisory_text": advisory_text
        }
        rendered_reply = self._template_engine.render(template_key, session.language, **render_kwargs)
        self._publish_event(
            SMSEventType.TEMPLATE_RENDERED.value,
            trace_id,
            session.conversation_id,
            {"template_key": template_key, "language": session.language}
        )
        return cast(str, rendered_reply)

    async def _deliver_outbound(
        self,
        sender_phone: str,
        rendered_reply: str,
        session: Any,
        trace_id: str,
        start_time: float
    ) -> dict[str, Any]:
        providers = self._registry.list_providers()
        if not providers:
            err_msg = "No active SMS provider adapters available."
            self._session_manager.close_session(session.sms_session_id)
            return {"success": False, "status": "failed", "error": err_msg}
        provider = providers[0]

        delivery_success = await provider.send_sms(sender_phone, rendered_reply)
        session.thread_history.append({"direction": "outbound", "text": rendered_reply, "timestamp": time.time()})
        latency_ms = round((time.perf_counter() - start_time) * 1000, 4)

        if delivery_success:
            self._publish_event(SMSEventType.SMS_SENT.value, trace_id, session.conversation_id, {})
            self._publish_event(SMSEventType.SMS_DELIVERED.value, trace_id, session.conversation_id, {})
            session.delivery_status = "delivered"
        else:
            self._publish_event(SMSEventType.SMS_FAILED.value, trace_id, session.conversation_id, {})
            session.delivery_status = "failed"

        # Record Telemetry Metrics
        if hasattr(self._container, "telemetry"):
            self._container.telemetry.record("sms_processing_latency_ms", latency_ms, trace_id, session.conversation_id)
            self._container.telemetry.record("sms_received_count", 1, trace_id, session.conversation_id)
            self._container.telemetry.record("sms_sent_count", 1, trace_id, session.conversation_id)
            self._container.telemetry.record("sms_retry_count", session.retry_count, trace_id, session.conversation_id)
            self._container.telemetry.record("sms_session_continuity", len(session.thread_history), trace_id, session.conversation_id)
            if not delivery_success:
                self._container.telemetry.record("sms_delivery_failure", 1, trace_id, session.conversation_id)

        return {
            "success": delivery_success,
            "sms_session_id": session.sms_session_id,
            "conversation_id": session.conversation_id,
            "rendered_reply": rendered_reply,
            "delivery_status": session.delivery_status,
            "latency_ms": latency_ms
        }

    def _validate_message(self, phone: str, text: str) -> list[str]:
        errors = []
        if len(text) > 800:
            errors.append("Message body length exceeds maximum threshold of 800 characters.")

        sensitive_keywords = [r"\bpin\b", r"\bpassword\b", r"\bcvv\b", r"\bcredit card\b", r"\bcard number\b"]
        for pattern in sensitive_keywords:
            if re.search(pattern, text.lower()):
                errors.append("Message contains sensitive information fields (PIN/CVV/Password/Card details).")
                break

        spam_reason = self._rate_limiter.is_spam(phone, text)
        if spam_reason:
            errors.append(f"Spam filter blocked: {spam_reason}")

        return errors

    def _publish_event(self, event_type: str, trace_id: str, session_id: str, payload: dict[str, Any]) -> None:
        if hasattr(self._container, "event_bus") and self._container.event_bus:
            try:
                from app.core.event_bus import Event
                self._container.event_bus.publish(Event(
                    event_type=event_type,
                    trace_id=trace_id,
                    request_id="sms_pipeline",
                    session_id=session_id,
                    payload=payload
                ))
            except Exception as e:
                logger.error(f"Failed to publish SMS event '{event_type}': {e}")

    def _determine_template(self, text: str, tags: list[str]) -> str:
        text_lower = text.lower()
        if "weather" in text_lower or "weather" in tags:
            return "weather_alert"
        if "price" in text_lower or "price" in tags:
            return "market_price"
        if "scheme" in text_lower or "scheme" in tags:
            return "gov_scheme"
        if "disease" in text_lower or "disease" in tags:
            return "crop_advisory"
        return "general"
