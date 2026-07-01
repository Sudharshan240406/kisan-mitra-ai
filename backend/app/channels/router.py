import asyncio
import logging
import time
from typing import Any

from app.channels.envelope import MessageEnvelope, ResponseEnvelope

logger = logging.getLogger("kisan_mitra_ai.channels.router")


class ChannelRouter:
    """
    Inbound message router that receives MessageEnvelopes, validates them,
    determines the channel, and forwards to the Conversation Platform.
    """
    def __init__(self, container: Any) -> None:
        self._container = container
        self._channel_registry = container.channel_registry
        self._session_manager = container.session_manager

    async def route_inbound(
        self,
        envelope: MessageEnvelope,
        asynchronous: bool = False
    ) -> ResponseEnvelope:
        """
        Validates, processes, and routes an inbound message envelope.
        Returns a ResponseEnvelope.
        """
        start_time = time.perf_counter()
        trace_id = envelope.trace_id or "unknown"
        session_id = envelope.conversation_id or "unknown"
        message_id = envelope.message_id or "unknown"

        # Validate envelope fields
        errors = self._validate_envelope(envelope)
        if errors:
            err_msg = f"Validation failed: {', '.join(errors)}"
            logger.warning(err_msg)
            self._publish_event(
                "error_occurred",
                trace_id=trace_id,
                session_id=session_id,
                payload={"error": err_msg, "channel": envelope.channel}
            )
            return ResponseEnvelope(
                message_id=message_id,
                conversation_id=session_id,
                channel=envelope.channel,
                receiver=envelope.sender,
                language=envelope.language,
                payload={"errors": errors},
                trace_id=trace_id,
                status="rejected"
            )

        # Verify channel exists and is active
        channel = self._channel_registry.discover(envelope.channel)
        if not channel:
            err_msg = f"Channel '{envelope.channel}' not registered."
            logger.warning(err_msg)
            self._publish_event(
                "error_occurred",
                trace_id=trace_id,
                session_id=session_id,
                payload={"error": err_msg, "channel": envelope.channel}
            )
            return ResponseEnvelope(
                message_id=message_id,
                conversation_id=session_id,
                channel=envelope.channel,
                receiver=envelope.sender,
                language=envelope.language,
                payload={"error": err_msg},
                trace_id=trace_id,
                status="rejected"
            )

        channel_type = channel.channel_metadata.channel_type.value

        # Find or create/touch a Session
        sessions = self._session_manager.list_sessions(envelope.channel)
        active_sessions = [
            s for s in sessions
            if s.conversation_id == envelope.conversation_id and s.state.value == "active"
        ]
        if not active_sessions:
            session = self._session_manager.create_session(
                conversation_id=envelope.conversation_id,
                channel_id=envelope.channel,
                channel_type=channel_type
            )
        else:
            session = active_sessions[0]
            session.touch()

        # Publish MessageReceived event
        self._publish_event(
            "message_received",
            trace_id=trace_id,
            session_id=session_id,
            payload={
                "message_id": message_id,
                "channel_id": envelope.channel,
                "channel_type": channel_type
            }
        )

        if asynchronous:
            # Queue for background processing
            asyncio.create_task(self._process_and_route_async(envelope, session.session_id))
            return ResponseEnvelope(
                message_id=message_id,
                conversation_id=session_id,
                channel=envelope.channel,
                receiver=envelope.sender,
                language=envelope.language,
                payload={"message": "Inbound message received and queued for asynchronous processing."},
                trace_id=trace_id,
                status="queued"
            )

        # Synchronous execution
        response_envelope = await self._process_and_route_sync(envelope)

        # Log latency & telemetry
        latency_ms = self._elapsed_ms(start_time)
        logger.info(f"Routed inbound envelope {message_id} in {latency_ms:.2f}ms")

        # Record Telemetry Metrics
        if hasattr(self._container, "telemetry"):
            self._container.telemetry.record(
                "channel_routing_latency_ms",
                latency_ms,
                trace_id=trace_id,
                session_id=session_id
            )
            self._container.telemetry.record(
                "channel_message_processed",
                1,
                trace_id=trace_id,
                session_id=session_id,
                metadata={"channel_id": envelope.channel, "channel_type": channel_type}
            )

        # Publish MessageProcessed event
        self._publish_event(
            "message_processed",
            trace_id=trace_id,
            session_id=session_id,
            payload={
                "message_id": message_id,
                "channel_id": envelope.channel,
                "latency_ms": latency_ms
            }
        )

        return response_envelope

    async def _process_and_route_sync(self, envelope: MessageEnvelope) -> ResponseEnvelope:
        """Helper to invoke orchestrator and route outbound response synchronously."""
        from app.orchestrator.orchestrator import AgentOrchestrator
        orchestrator = AgentOrchestrator(self._container)
        response_envelope = await orchestrator.execute_envelope(envelope)

        # Route outbound response envelope
        await self._container.response_router.route_outbound(response_envelope)
        return response_envelope

    async def _process_and_route_async(self, envelope: MessageEnvelope, session_id: str) -> None:
        """Helper to process envelope asynchronously."""
        try:
            start_time = time.perf_counter()
            await self._process_and_route_sync(envelope)

            # Record Telemetry Metrics
            latency_ms = self._elapsed_ms(start_time)
            if hasattr(self._container, "telemetry"):
                self._container.telemetry.record(
                    "channel_routing_latency_ms",
                    latency_ms,
                    trace_id=envelope.trace_id or "async",
                    session_id=envelope.conversation_id
                )
                self._container.telemetry.record(
                    "channel_message_processed",
                    1,
                    trace_id=envelope.trace_id or "async",
                    session_id=envelope.conversation_id,
                    metadata={"channel_id": envelope.channel}
                )

            # Publish MessageProcessed event
            self._publish_event(
                "message_processed",
                trace_id=envelope.trace_id or "async",
                session_id=envelope.conversation_id,
                payload={
                    "message_id": envelope.message_id,
                    "channel_id": envelope.channel,
                    "latency_ms": latency_ms,
                    "asynchronous": True
                }
            )
        except Exception as e:
            logger.error(f"Async processing of message {envelope.message_id} failed: {e}")
            self._publish_event(
                "error_occurred",
                trace_id=envelope.trace_id or "async",
                session_id=envelope.conversation_id,
                payload={"error": str(e), "message_id": envelope.message_id}
            )

    def _validate_envelope(self, envelope: MessageEnvelope) -> list[str]:
        """Validates required envelope fields."""
        errors: list[str] = []
        if not envelope.conversation_id:
            errors.append("Missing conversation_id.")
        if not envelope.channel:
            errors.append("Missing channel.")
        if not envelope.sender:
            errors.append("Missing sender.")
        return errors

    def _publish_event(self, event_type: str, trace_id: str, session_id: str, payload: dict[str, Any]) -> None:
        if hasattr(self._container, "event_bus") and self._container.event_bus:
            try:
                from app.core.event_bus import Event
                self._container.event_bus.publish(Event(
                    event_type=event_type,
                    trace_id=trace_id,
                    request_id="router",
                    session_id=session_id,
                    payload=payload
                ))
            except Exception as e:
                logger.error(f"Failed to publish event '{event_type}': {e}")

    @staticmethod
    def _elapsed_ms(start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 4)


class ResponseRouter:
    """
    Outbound response router that delivers ResponseEnvelopes back to originating channels.
    """
    def __init__(self, container: Any) -> None:
        self._container = container
        self._channel_registry = container.channel_registry

    async def route_outbound(self, response: ResponseEnvelope) -> dict[str, Any]:
        """
        Routes a response envelope back to its originating channel.
        """
        start_time = time.perf_counter()
        trace_id = response.trace_id or "unknown"
        session_id = response.conversation_id or "unknown"

        # Publish response generated event
        self._publish_event(
            "response_generated",
            trace_id=trace_id,
            session_id=session_id,
            payload={
                "response_id": response.response_id,
                "message_id": response.message_id,
                "channel_id": response.channel
            }
        )

        channel = self._channel_registry.discover(response.channel)
        if not channel:
            err_msg = f"Channel '{response.channel}' not registered."
            logger.warning(err_msg)

            # Publish error event
            self._publish_event(
                "error_occurred",
                trace_id=trace_id,
                session_id=session_id,
                payload={"error": err_msg, "channel": response.channel}
            )

            if hasattr(self._container, "telemetry"):
                self._container.telemetry.record(
                    "channel_delivery_error",
                    1,
                    trace_id=trace_id,
                    session_id=session_id,
                    metadata={"channel_id": response.channel, "reason": "not_registered"}
                )

            return {
                "status": "undeliverable",
                "reason": err_msg,
                "response_id": response.response_id,
                "latency_ms": self._elapsed_ms(start_time)
            }

        # Framework-only: simulate delivery
        delivered = await channel.send(response.receiver, response.payload)

        latency_ms = self._elapsed_ms(start_time)

        if delivered:
            # Publish response delivered event
            self._publish_event(
                "response_delivered",
                trace_id=trace_id,
                session_id=session_id,
                payload={
                    "response_id": response.response_id,
                    "message_id": response.message_id,
                    "channel_id": response.channel,
                    "latency_ms": latency_ms
                }
            )

            # Record telemetry metrics
            if hasattr(self._container, "telemetry"):
                self._container.telemetry.record(
                    "channel_response_time_ms",
                    latency_ms,
                    trace_id=trace_id,
                    session_id=session_id
                )
        else:
            err_msg = f"Delivery failed on channel '{response.channel}'."
            logger.warning(err_msg)

            # Publish error event
            self._publish_event(
                "error_occurred",
                trace_id=trace_id,
                session_id=session_id,
                payload={"error": err_msg, "channel": response.channel}
            )

            if hasattr(self._container, "telemetry"):
                self._container.telemetry.record(
                    "channel_delivery_error",
                    1,
                    trace_id=trace_id,
                    session_id=session_id,
                    metadata={"channel_id": response.channel, "reason": "send_failed"}
                )

        return {
            "status": "delivered" if delivered else "failed",
            "response_id": response.response_id,
            "channel": response.channel,
            "receiver": response.receiver,
            "latency_ms": latency_ms
        }

    def _publish_event(self, event_type: str, trace_id: str, session_id: str, payload: dict[str, Any]) -> None:
        if hasattr(self._container, "event_bus") and self._container.event_bus:
            try:
                from app.core.event_bus import Event
                self._container.event_bus.publish(Event(
                    event_type=event_type,
                    trace_id=trace_id,
                    request_id="router",
                    session_id=session_id,
                    payload=payload
                ))
            except Exception as e:
                logger.error(f"Failed to publish event '{event_type}': {e}")

    @staticmethod
    def _elapsed_ms(start: float) -> float:
        return round((time.perf_counter() - start) * 1000, 4)
