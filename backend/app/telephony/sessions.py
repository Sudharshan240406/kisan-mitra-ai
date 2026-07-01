import logging
import time
from enum import Enum
from typing import Any, Optional

from app.utils.id import generate_uuid
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.telephony.sessions")


class CallSessionState(str, Enum):
    """Call session operational state codes."""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    CLOSED = "closed"
    RECOVERED = "recovered"


class CallSession(BaseModel):
    """
    Session object tracking a single telephone call interaction lifecycle.
    """
    call_id: str = Field(..., description="Unique call identifier.")
    conversation_id: str = Field(default_factory=generate_uuid, description="Linked conversation/chat reference.")
    language: str = Field(default="hi", description="Current selected language (hi, pa, en).")
    current_ivr_state: str = Field(default="GREETING", description="Active state in the IVR state machine.")
    state: CallSessionState = Field(default=CallSessionState.ACTIVE, description="Lifecycle state.")
    created_at: float = Field(default_factory=time.time, description="Creation epoch timestamp.")
    last_activity: float = Field(default_factory=time.time, description="Last activity timestamp.")
    timeout_seconds: int = Field(default=300, description="Inactivity timeout window in seconds (default 5 min).")
    dtmf_buffer: str = Field(default="", description="Accumulated DTMF digits pressed.")
    recording_metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata for call recordings.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata values.")
    recovery_count: int = Field(default=0, description="Track recovery retries count.")

    def is_expired(self) -> bool:
        """Checks if session has timed out."""
        return (time.time() - self.last_activity) > self.timeout_seconds

    def touch(self) -> None:
        """Keeps session alive by updating last activity time."""
        self.last_activity = time.time()
        if self.state == CallSessionState.IDLE:
            self.state = CallSessionState.ACTIVE


class CallSessionManager:
    """
    Manager class handling creation, timeouts, recovery, and cleanup of Call Sessions.
    """
    def __init__(self, event_bus: Optional[Any] = None) -> None:
        self._sessions: dict[str, CallSession] = {}
        self._event_bus = event_bus

    def create_session(
        self,
        call_id: str,
        conversation_id: Optional[str] = None,
        language: str = "hi",
        timeout_seconds: int = 300,
        metadata: Optional[dict[str, Any]] = None
    ) -> CallSession:
        """Creates and tracks a new CallSession."""
        session = CallSession(
            call_id=call_id,
            conversation_id=conversation_id or f"CONV-CALL-{generate_uuid()[:8]}",
            language=language,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {}
        )
        self._sessions[call_id] = session
        logger.info(f"Call Session '{call_id}' started for conversation '{session.conversation_id}'.")

        self._publish_event("telephony_session_started", session)
        return session

    def get_session(self, call_id: str) -> Optional[CallSession]:
        """Retrieves and touches a call session by ID, marking it expired if timed out."""
        session = self._sessions.get(call_id)
        if session:
            if session.is_expired() and session.state == CallSessionState.ACTIVE:
                session.state = CallSessionState.EXPIRED
                logger.info(f"Call Session '{call_id}' has expired.")
                self._publish_event("telephony_session_expired", session)
            else:
                session.touch()
        return session

    def recover_session(self, call_id: str) -> Optional[CallSession]:
        """Recovers an expired session, moving it back to RECOVERED/ACTIVE state."""
        session = self._sessions.get(call_id)
        if not session:
            return None
        session.state = CallSessionState.RECOVERED
        session.recovery_count += 1
        session.touch()
        logger.info(f"Call Session '{call_id}' successfully recovered (Count: {session.recovery_count}).")
        self._publish_event("telephony_session_recovered", session)
        return session

    def close_session(self, call_id: str) -> None:
        """Closes an active session."""
        session = self._sessions.get(call_id)
        if session:
            session.state = CallSessionState.CLOSED
            logger.info(f"Call Session '{call_id}' closed.")
            self._publish_event("telephony_session_ended", session)

    def cleanup_expired(self) -> int:
        """Runs expiration checks, changing state of timed-out active sessions."""
        count = 0
        for session in self._sessions.values():
            if session.state == CallSessionState.ACTIVE and session.is_expired():
                session.state = CallSessionState.EXPIRED
                count += 1
                self._publish_event("telephony_session_expired", session)
        return count

    def list_sessions(self) -> list[CallSession]:
        return list(self._sessions.values())

    def _publish_event(self, event_type: str, session: CallSession) -> None:
        if self._event_bus:
            try:
                from app.core.event_bus import Event
                self._event_bus.publish(Event(
                    event_type=event_type,
                    trace_id=f"call_{session.call_id}",
                    request_id="session_manager",
                    session_id=session.conversation_id,
                    payload={
                        "call_id": session.call_id,
                        "conversation_id": session.conversation_id,
                        "state": session.state.value,
                        "current_ivr_state": session.current_ivr_state
                    }
                ))
            except Exception as e:
                logger.error(f"Failed to publish call event '{event_type}': {e}")
