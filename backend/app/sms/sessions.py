import logging
import time
from enum import Enum
from typing import Any, Optional

from app.utils.id import generate_uuid
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.sms.sessions")


class SMSSessionState(str, Enum):
    """SMS session operational lifecycle states."""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    CLOSED = "closed"
    RECOVERED = "recovered"


class SMSSession(BaseModel):
    """
    Session object tracking a single SMS conversation thread interaction.
    """
    sms_session_id: str = Field(default_factory=generate_uuid, description="Unique SMS session identifier.")
    conversation_id: str = Field(default_factory=generate_uuid, description="Linked conversation/chat reference.")
    farmer_id: str = Field(default="unknown-farmer", description="Farmer profile database reference ID.")
    phone_number: str = Field(..., description="Farmer phone number.")
    language: str = Field(default="hi", description="Preferred language (hi, en, kn, te, ta).")
    thread_history: list[dict[str, Any]] = Field(default_factory=list, description="Threaded messages history logs.")
    delivery_status: str = Field(default="queued", description="Outbound delivery transaction status.")
    retry_count: int = Field(default=0, description="Outbound retry count.")
    state: SMSSessionState = Field(default=SMSSessionState.ACTIVE, description="Lifecycle operational state.")
    created_at: float = Field(default_factory=time.time, description="Creation epoch timestamp.")
    last_activity: float = Field(default_factory=time.time, description="Last activity timestamp.")
    timeout_seconds: int = Field(default=86400, description="SMS threads timeout (default 24h).")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata properties.")

    def is_expired(self) -> bool:
        """Checks if session has timed out."""
        return (time.time() - self.last_activity) > self.timeout_seconds

    def touch(self) -> None:
        """Keeps session alive by updating last activity time."""
        self.last_activity = time.time()
        if self.state == SMSSessionState.IDLE:
            self.state = SMSSessionState.ACTIVE


class SMSSessionManager:
    """
    Manager class handling creation, timeouts, recovery, and cleanup of SMS Sessions.
    """
    def __init__(self, event_bus: Optional[Any] = None) -> None:
        self._sessions: dict[str, SMSSession] = {}
        self._phone_to_session: dict[str, str] = {}
        self._event_bus = event_bus

    def create_session(
        self,
        phone_number: str,
        farmer_id: str = "unknown-farmer",
        language: str = "hi",
        conversation_id: Optional[str] = None,
        timeout_seconds: int = 86400,
        metadata: Optional[dict[str, Any]] = None
    ) -> SMSSession:
        """Creates and tracks a new SMSSession."""
        conv_id = conversation_id or f"CONV-SMS-{generate_uuid()[:8]}"
        session = SMSSession(
            phone_number=phone_number,
            farmer_id=farmer_id,
            language=language,
            conversation_id=conv_id,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {}
        )
        self._sessions[session.sms_session_id] = session
        self._phone_to_session[phone_number] = session.sms_session_id
        logger.info(f"SMS Session '{session.sms_session_id}' started for phone '{phone_number}'.")

        self._publish_event("sms_session_started", session)
        return session

    def get_session(self, sms_session_id: str) -> Optional[SMSSession]:
        """Retrieves and touches an SMS session by ID."""
        session = self._sessions.get(sms_session_id)
        if session:
            if session.is_expired() and session.state == SMSSessionState.ACTIVE:
                session.state = SMSSessionState.EXPIRED
                logger.info(f"SMS Session '{sms_session_id}' has expired.")
                self._publish_event("sms_session_expired", session)
            else:
                session.touch()
        return session

    def get_session_by_phone(self, phone_number: str) -> Optional[SMSSession]:
        """Retrieves or finds active session by farmer phone number."""
        sess_id = self._phone_to_session.get(phone_number)
        if not sess_id:
            return None
        return self.get_session(sess_id)

    def recover_session(self, sms_session_id: str) -> Optional[SMSSession]:
        """Recovers an expired session, moving it back to RECOVERED/ACTIVE state."""
        session = self._sessions.get(sms_session_id)
        if not session:
            return None
        session.state = SMSSessionState.RECOVERED
        session.retry_count += 1
        session.touch()
        logger.info(f"SMS Session '{sms_session_id}' successfully recovered (Count: {session.retry_count}).")
        self._publish_event("sms_session_recovered", session)
        return session

    def close_session(self, sms_session_id: str) -> None:
        """Closes an active session."""
        session = self._sessions.get(sms_session_id)
        if session:
            session.state = SMSSessionState.CLOSED
            if session.phone_number in self._phone_to_session:
                del self._phone_to_session[session.phone_number]
            logger.info(f"SMS Session '{sms_session_id}' closed.")
            self._publish_event("sms_session_ended", session)

    def cleanup_expired(self) -> int:
        """Runs expiration checks, changing state of timed-out active sessions."""
        count = 0
        for session in self._sessions.values():
            if session.state == SMSSessionState.ACTIVE and session.is_expired():
                session.state = SMSSessionState.EXPIRED
                count += 1
                self._publish_event("sms_session_expired", session)
        return count

    def list_sessions(self) -> list[SMSSession]:
        return list(self._sessions.values())

    def _publish_event(self, event_type: str, session: SMSSession) -> None:
        if self._event_bus:
            try:
                from app.core.event_bus import Event
                self._event_bus.publish(Event(
                    event_type=event_type,
                    trace_id=f"sms_{session.sms_session_id[:8]}",
                    request_id="session_manager",
                    session_id=session.conversation_id,
                    payload={
                        "sms_session_id": session.sms_session_id,
                        "conversation_id": session.conversation_id,
                        "phone_number": session.phone_number,
                        "state": session.state.value
                    }
                ))
            except Exception as e:
                logger.error(f"Failed to publish SMS event '{event_type}': {e}")
