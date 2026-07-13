import logging
from typing import Any, Optional

from app.channels.envelope import LanguageMetadata, MessageEnvelope, MessagePriority
from app.utils.id import generate_uuid

logger = logging.getLogger("kisan_mitra_ai.sms.inbound_router")


class InboundRouter:
    """Handles incoming SMS, routes them through the AI Orchestrator, and returns the response."""

    def __init__(self, container: Any) -> None:
        self.container = container

    async def handle_inbound_sms(self, sender: str, body: str) -> Optional[str]:
        logger.info(f"[InboundRouter] Received inbound SMS from {sender}: {body}")

        # 1. Identify Farmer & Digital Twin / Language
        farmer_id = "guest_farmer"
        farmer_name = "Farmer Ramesh"
        language = "hi"
        try:
            from app.services.demo import DemoService
            demo_service = DemoService()
            farmer = demo_service.get_farmer_by_phone(sender)
            if not farmer:
                all_farmers = demo_service.get_all_farmers()
                farmer = all_farmers[0] if all_farmers else None

            if farmer:
                farmer_id = farmer.farmer_id
                farmer_name = farmer.name
                language = farmer.preferred_language or "hi"
        except Exception as e:
            logger.warning(f"Could not resolve farmer profile for {sender}: {e}")

        conversation_id = f"sms-conv-{sender.replace('+', '')}"
        trace_id = f"sms-trace-{generate_uuid()}"

        # Broadcast live incoming SMS to Mission Control Dashboard
        try:
            import asyncio

            from app.api.v1.websocket import ws_manager
            asyncio.create_task(ws_manager.push_event("SMS_TELEMETRY", {
                "direction": "inbound",
                "sms_id": generate_uuid(),
                "recipient": "system",
                "body": body,
                "status": "received",
                "provider": "carrier",
                "latency_ms": 0.0,
                "retry_count": 0,
                "farmer_name": farmer_name,
                "farmer_id": farmer_id
            }))
        except Exception:
            pass

        # 2. Build Message Envelope
        lang_metadata = LanguageMetadata(
            preferred_language=language,
            locale=language
        )

        envelope = MessageEnvelope(
            conversation_id=conversation_id,
            channel="sms-001",
            sender=sender,
            receiver="system",
            language=lang_metadata,
            payload={"text": body},
            priority=MessagePriority.NORMAL,
            trace_id=trace_id
        )

        # 3. Route to AI Orchestrator
        advisory_text = ""
        try:
            router = getattr(self.container, "channel_router", None)
            if router:
                response = await router.route_inbound(envelope, asynchronous=False)
                if response and response.payload:
                    advisory_text = (
                        response.payload.get("recommendation")
                        or response.payload.get("text")
                        or ""
                    )

            if not advisory_text:
                advisory_text = "Thank you for your message. We are processing your request."
        except Exception as e:
            logger.error(f"Failed to route SMS to AI Orchestrator: {e}", exc_info=True)
            advisory_text = "Sorry, advisory services are currently busy. Please try again."

        # 4. Reply to Farmer via SMSManager
        try:
            sms_manager = getattr(self.container, "sms_manager", None)
            if sms_manager:
                await sms_manager.send_sms(
                    recipient=sender,
                    body=advisory_text,
                    language=language
                )
        except Exception as e:
            logger.error(f"Failed to send SMS reply: {e}")

        return advisory_text
