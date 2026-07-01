import logging
import time
from collections.abc import Callable
from typing import Any

from app.utils.id import generate_uuid
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai")

class Event(BaseModel):
    """
    Standard event packet passed via the EventBus containing trace keys and payloads.
    """
    event_id: str = Field(default_factory=generate_uuid, description="Unique event tracker ID.")
    event_type: str = Field(..., description="Logical type code representing the event trigger.")
    timestamp: float = Field(default_factory=time.time, description="Publish epoch timestamp.")
    trace_id: str = Field(..., description="Request trace ID propagating log correlation.")
    request_id: str = Field(..., description="Source request ID.")
    session_id: str = Field(..., description="Active session ID.")
    payload: dict[str, Any] = Field(default_factory=dict, description="Arbitrary payload carrying context parameters.")

class EventBus:
    """
    Lightweight in-memory event bus managing agent/orchestrator events,
    history tracing, message replays, and component subscriptions.
    """
    def __init__(self) -> None:
        self._subscriptions: dict[str, list[Callable[[Event], Any]]] = {}
        self._history: list[Event] = []
        logger.info("Platform EventBus successfully initialized.")

    def subscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """
        Subscribes a callback handler to a specific event type.
        """
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        if handler not in self._subscriptions[event_type]:
            self._subscriptions[event_type].append(handler)
            logger.info(f"Handler '{handler.__name__}' subscribed to event '{event_type}'.")

    def unsubscribe(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """
        Unsubscribes a callback handler from a specific event type.
        """
        if event_type in self._subscriptions:
            try:
                self._subscriptions[event_type].remove(handler)
                logger.info(f"Handler '{handler.__name__}' unsubscribed from event '{event_type}'.")
            except ValueError:
                pass

    def publish(self, event: Event) -> None:
        """
        Publishes an event to all active subscribers, records it in history, and logs it.
        """
        self._history.append(event)

        # Format tracing log context
        logger.info(
            f"[EventBus] PUBLISH event_type='{event.event_type}' event_id='{event.event_id}' "
            f"(Trace: {event.trace_id}, Request: {event.request_id}, Session: {event.session_id})"
        )

        # Trigger registered event-specific handlers
        handlers = self._subscriptions.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"[EventBus] Handler '{handler.__name__}' failed during event '{event.event_type}': {e!s}"
                )

        # Trigger wildcard handlers (subscribing to '*')
        wildcards = self._subscriptions.get("*", [])
        for handler in wildcards:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"[EventBus] Wildcard handler '{handler.__name__}' failed during event '{event.event_type}': {e!s}"
                )

    def get_history(self, trace_id: str | None = None) -> list[Event]:
        """
        Retrieve historical logs, optionally filtered by a specific trace_id.
        """
        if trace_id:
            return [e for e in self._history if e.trace_id == trace_id]
        return list(self._history)

    def replay(self, trace_id: str | None = None) -> None:
        """
        Replay event notifications matching a specific trace (or all history) to active subscribers.
        """
        events_to_replay = self.get_history(trace_id)
        logger.info(f"[EventBus] Replaying {len(events_to_replay)} historical events...")
        for event in events_to_replay:
            # Trigger handlers again
            handlers = self._subscriptions.get(event.event_type, [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    logger.error(f"[EventBus Replay] Handler failed: {e!s}")

    def health(self) -> dict[str, Any]:
        """
        Exposes health metrics for the Event Bus.
        """
        return {
            "status": "healthy",
            "subscription_types_count": len(self._subscriptions),
            "history_depth": len(self._history),
            "wildcard_handlers_count": len(self._subscriptions.get("*", []))
        }
