import logging
import time
from enum import Enum
from typing import Any, Optional, Dict, List
from pydantic import BaseModel, Field
from app.utils.id import generate_uuid

logger = logging.getLogger("kisan_mitra_ai.ivr.call_session")


class CallSessionState(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    CLOSED = "closed"
    RECOVERED = "recovered"


class TranscriptEntry(BaseModel):
    sender: str  # "farmer" or "system"
    text: str
    timestamp: float = Field(default_factory=time.time)
    confidence: float = 1.0
    execution_id: Optional[str] = None
    timing_ms: float = 0.0


class CallSummaryModel(BaseModel):
    conversation_summary: str = ""
    recommended_schemes: List[str] = Field(default_factory=list)
    weather_advice: str = ""
    market_advice: str = ""
    action_items: List[str] = Field(default_factory=list)


class CallSession(BaseModel):
    call_id: str = Field(..., description="Unique call identifier.")
    conversation_id: str = Field(default_factory=generate_uuid, description="Linked conversation/chat reference.")
    language: str = Field(default="hi", description="Current selected language (hi, en, kn, te, ta, pa).")
    current_ivr_state: str = Field(default="GREETING", description="Active state in the IVR state machine.")
    state: CallSessionState = Field(default=CallSessionState.ACTIVE, description="Lifecycle state.")
    created_at: float = Field(default_factory=time.time, description="Creation epoch timestamp.")
    last_activity: float = Field(default_factory=time.time, description="Last activity timestamp.")
    timeout_seconds: int = Field(default=300, description="Inactivity timeout window in seconds.")
    dtmf_buffer: str = Field(default="", description="Accumulated DTMF digits pressed.")
    farmer_id: Optional[str] = Field(default=None, description="Linked farmer profile ID from Digital Twin.")
    farmer_profile_snapshot: Dict[str, Any] = Field(default_factory=dict, description="Cached farmer profile data.")
    recording_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata for call recordings.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata values.")
    recovery_count: int = Field(default=0, description="Track recovery retries count.")
    transcript: List[TranscriptEntry] = Field(default_factory=list, description="Call conversation transcript.")
    summary: Optional[CallSummaryModel] = Field(default=None, description="Call summary information.")

    def is_expired(self) -> bool:
        return (time.time() - self.last_activity) > self.timeout_seconds

    def touch(self) -> None:
        self.last_activity = time.time()
        if self.state == CallSessionState.IDLE:
            self.state = CallSessionState.ACTIVE


class CallSessionManager:
    """Manages creation, retrieval, and cleanup of Call Sessions in memory."""
    def __init__(self, event_bus: Optional[Any] = None) -> None:
        self._sessions: Dict[str, CallSession] = {}
        self._event_bus = event_bus

    def create_session(
        self,
        call_id: str,
        conversation_id: Optional[str] = None,
        language: str = "hi",
        timeout_seconds: int = 300,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CallSession:
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
        session = self._sessions.get(call_id)
        if session:
            if session.is_expired() and session.state == CallSessionState.ACTIVE:
                session.state = CallSessionState.EXPIRED
                logger.info(f"Call Session '{call_id}' expired.")
                self._publish_event("telephony_session_expired", session)
            else:
                session.touch()
        return session

    def recover_session(self, call_id: str) -> Optional[CallSession]:
        session = self._sessions.get(call_id)
        if not session:
            return None
        session.state = CallSessionState.RECOVERED
        session.recovery_count += 1
        session.touch()
        logger.info(f"Call Session '{call_id}' recovered (Count: {session.recovery_count}).")
        self._publish_event("telephony_session_recovered", session)
        return session

    def close_session(self, call_id: str) -> None:
        session = self._sessions.get(call_id)
        if session:
            session.state = CallSessionState.CLOSED
            logger.info(f"Call Session '{call_id}' closed.")
            self._publish_event("telephony_session_ended", session)

    def cleanup_expired(self) -> int:
        count = 0
        for session in self._sessions.values():
            if session.state == CallSessionState.ACTIVE and session.is_expired():
                session.state = CallSessionState.EXPIRED
                count += 1
                self._publish_event("telephony_session_expired", session)
        return count

    def list_sessions(self) -> List[CallSession]:
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
