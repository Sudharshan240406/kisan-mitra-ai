import logging
from typing import Any
from app.channels.envelope import LanguageMetadata, MessageEnvelope, MessagePriority

logger = logging.getLogger("kisan_mitra_ai.ivr.call_router")


class CallRouter:
    """Routes voice query transcripts through Kisan Mitra AI Orchestrator."""

    def __init__(self, container: Any) -> None:
        self.container = container

    async def route_query(self, session: Any, query: str) -> str:
        trace_id = session.metadata.get("trace_id", "ivr_trace")
        logger.info(f"[Call {session.call_id}] Routing query to orchestrator: {query}")

        lang_metadata = LanguageMetadata(
            preferred_language=session.language,
            locale=session.language
        )
        
        envelope = MessageEnvelope(
            conversation_id=session.conversation_id,
            channel="ivr-001",  # Standard IVR channel ID
            sender=session.metadata.get("caller", "farmer-telephony"),
            receiver="system",
            language=lang_metadata,
            payload={"text": query},
            priority=MessagePriority.HIGH,
            trace_id=trace_id
        )

        advisory_text = ""
        try:
            # Route using the DI container channel_router
            router = getattr(self.container, "channel_router", None)
            if router:
                response = await router.route_inbound(envelope, asynchronous=False)
                if response and response.payload:
                    advisory_text = (
                        response.payload.get("recommendation")
                        or response.payload.get("text")
                        or ""
                    )
                else:
                    advisory_text = "Sorry, I could not generate a recommendation at this moment."
            else:
                # If no channel router registered, return fallback warning
                logger.warning("No channel_router found in container.")
                advisory_text = "Advisory services are currently unavailable."
        except Exception as e:
            logger.error(f"Failed to query advisory orchestrator: {e}", exc_info=True)
            advisory_text = "An error occurred while generating your recommendation."

        return advisory_text
