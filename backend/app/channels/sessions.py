import logging
import time
from enum import Enum
from typing import Any, Optional

from app.utils.id import generate_uuid
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.channels.sessions")


class SessionState(str, Enum):
    """Session lifecycle states."""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    RECOVERED = "recovered"
    CLOSED = "closed"


class ChannelSession(BaseModel):
    """
    Communication session tracking lifecycle, timeout, and metadata.
    """
    session_id: str = Field(default_factory=generate_uuid, description="Unique session identifier.")
    conversation_id: str = Field(..., description="Linked conversation ID.")
    channel_id: str = Field(..., description="Originating channel identifier.")
    channel_type: str = Field(default="web_chat", description="Channel type label.")
    farmer_id: Optional[str] = Field(default=None, description="Farmer profile reference.")
    state: SessionState = Field(default=SessionState.ACTIVE, description="Current lifecycle state.")
    created_at: float = Field(default_factory=time.time, description="Session creation epoch.")
    last_activity: float = Field(default_factory=time.time, description="Last interaction epoch.")
    timeout_seconds: int = Field(default=1800, description="Session timeout in seconds (default 30 min).")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible session metadata.")

    def is_expired(self) -> bool:
        """Checks whether the session has exceeded its timeout window."""
        return (time.time() - self.last_activity) > self.timeout_seconds

    def touch(self) -> None:
        """Updates last activity timestamp to keep session alive."""
        self.last_activity = time.time()
        if self.state == SessionState.IDLE:
            self.state = SessionState.ACTIVE


class SessionManager:
    """
    Manages communication session lifecycle across all channel types.
    """
    def __init__(self, event_bus: Optional[Any] = None) -> None:
        self._sessions: dict[str, ChannelSession] = {}
        self._event_bus = event_bus

    def create_session(
        self,
        conversation_id: str,
        channel_id: str,
        channel_type: str = "web_chat",
        farmer_id: Optional[str] = None,
        timeout_seconds: int = 1800
    ) -> ChannelSession:
        """Creates a new communication session."""
        # Determine default timeout based on channel type if the default 1800 is passed
        if timeout_seconds == 1800:
            if channel_type in ("voice", "ivr"):
                timeout_seconds = 300
            elif channel_type in ("sms", "whatsapp"):
                timeout_seconds = 86400

        session = ChannelSession(
            conversation_id=conversation_id,
            channel_id=channel_id,
            channel_type=channel_type,
            farmer_id=farmer_id,
            timeout_seconds=timeout_seconds
        )
        self._sessions[session.session_id] = session
        logger.info(f"Session '{session.session_id}' created for channel '{channel_id}'.")

        if self._event_bus:
            try:
                from app.channels.events import ChannelEventType
                from app.core.event_bus import Event
                self._event_bus.publish(Event(
                    event_type=ChannelEventType.SESSION_STARTED.value,
                    trace_id="session_lifecycle",
                    request_id="session_lifecycle",
                    session_id=session.session_id,
                    payload={
                        "session_id": session.session_id,
                        "conversation_id": session.conversation_id,
                        "channel_id": session.channel_id,
                        "channel_type": session.channel_type
                    }
                ))
            except Exception as e:
                logger.error(f"Failed to publish session started event: {e}")

        return session

    def get_session(self, session_id: str) -> Optional[ChannelSession]:
        """Retrieves a session by ID."""
        session = self._sessions.get(session_id)
        if session and session.is_expired() and session.state == SessionState.ACTIVE:
            session.state = SessionState.EXPIRED
            logger.info(f"Session '{session_id}' has expired.")

            if self._event_bus:
                try:
                    from app.channels.events import ChannelEventType
                    from app.core.event_bus import Event
                    self._event_bus.publish(Event(
                        event_type=ChannelEventType.SESSION_EXPIRED.value,
                        trace_id="session_lifecycle",
                        request_id="session_lifecycle",
                        session_id=session.session_id,
                        payload={
                            "session_id": session.session_id,
                            "conversation_id": session.conversation_id,
                            "channel_id": session.channel_id
                        }
                    ))
                except Exception as e:
                    logger.error(f"Failed to publish session expired event: {e}")

        return session

    def recover_session(self, session_id: str) -> Optional[ChannelSession]:
        """Recovers an expired session if it still exists."""
        session = self._sessions.get(session_id)
        if not session:
            return None
        session.state = SessionState.RECOVERED
        session.touch()
        logger.info(f"Session '{session_id}' recovered.")

        if self._event_bus:
            try:
                from app.channels.events import ChannelEventType
                from app.core.event_bus import Event
                self._event_bus.publish(Event(
                    event_type=ChannelEventType.SESSION_RECOVERED.value,
                    trace_id="session_lifecycle",
                    request_id="session_lifecycle",
                    session_id=session.session_id,
                    payload={
                        "session_id": session.session_id,
                        "conversation_id": session.conversation_id,
                        "channel_id": session.channel_id
                    }
                ))
            except Exception as e:
                logger.error(f"Failed to publish session recovered event: {e}")

        return session

    def close_session(self, session_id: str) -> None:
        """Closes a session."""
        session = self._sessions.get(session_id)
        if session:
            session.state = SessionState.CLOSED
            logger.info(f"Session '{session_id}' closed.")

            if self._event_bus:
                try:
                    from app.channels.events import ChannelEventType
                    from app.core.event_bus import Event
                    self._event_bus.publish(Event(
                        event_type=ChannelEventType.SESSION_ENDED.value,
                        trace_id="session_lifecycle",
                        request_id="session_lifecycle",
                        session_id=session.session_id,
                        payload={
                            "session_id": session.session_id,
                            "conversation_id": session.conversation_id,
                            "channel_id": session.channel_id
                        }
                    ))
                except Exception as e:
                    logger.error(f"Failed to publish session ended event: {e}")

    def list_sessions(self, channel_id: Optional[str] = None) -> list[ChannelSession]:
        """Lists sessions, optionally filtered by channel."""
        sessions = list(self._sessions.values())
        if channel_id:
            return [s for s in sessions if s.channel_id == channel_id]
        return sessions

    def cleanup_expired(self) -> int:
        """Expires all timed-out sessions. Returns count of expired."""
        count = 0
        for session in self._sessions.values():
            if session.state == SessionState.ACTIVE and session.is_expired():
                session.state = SessionState.EXPIRED
                count += 1

                if self._event_bus:
                    try:
                        from app.channels.events import ChannelEventType
                        from app.core.event_bus import Event
                        self._event_bus.publish(Event(
                            event_type=ChannelEventType.SESSION_EXPIRED.value,
                            trace_id="session_lifecycle",
                            request_id="session_lifecycle",
                            session_id=session.session_id,
                            payload={
                                "session_id": session.session_id,
                                "conversation_id": session.conversation_id,
                                "channel_id": session.channel_id
                            }
                        ))
                    except Exception as e:
                        logger.error(f"Failed to publish session expired event during cleanup: {e}")
        return count
