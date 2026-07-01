import logging
import time
from enum import Enum
from typing import Any, Optional

from app.utils.id import generate_uuid
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.media.sessions")


class MediaSessionState(str, Enum):
    """Media session lifecycle states."""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    CLOSED = "closed"
    RECOVERED = "recovered"


class MediaSession(BaseModel):
    """
    Session object tracking a single media processing interaction lifecycle.
    """
    media_session_id: str = Field(default_factory=generate_uuid, description="Unique media session identifier.")
    conversation_id: str = Field(..., description="Linked conversation/chat reference.")
    media_type: str = Field(..., description="Classification of associated media.")
    language: str = Field(default="hi", description="Preferred language locale code.")
    state: MediaSessionState = Field(default=MediaSessionState.ACTIVE, description="Lifecycle state.")
    created_at: float = Field(default_factory=time.time, description="Creation epoch timestamp.")
    last_activity: float = Field(default_factory=time.time, description="Last activity timestamp.")
    timeout_seconds: int = Field(default=600, description="Inactivity timeout window in seconds (default 10 min).")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible metadata values.")
    streaming_placeholder: dict[str, Any] = Field(default_factory=dict, description="Buffer segment references for future streaming support.")
    recovery_count: int = Field(default=0, description="Track recovery retries count.")

    def is_expired(self) -> bool:
        """Checks if session has timed out."""
        return (time.time() - self.last_activity) > self.timeout_seconds

    def touch(self) -> None:
        """Keeps session alive by updating last activity time."""
        self.last_activity = time.time()
        if self.state == MediaSessionState.IDLE:
            self.state = MediaSessionState.ACTIVE


class MediaSessionManager:
    """
    Manager class handling creation, timeouts, recovery, and cleanup of Media Sessions.
    """
    def __init__(self, event_bus: Optional[Any] = None) -> None:
        self._sessions: dict[str, MediaSession] = {}
        self._event_bus = event_bus

    def create_session(
        self,
        conversation_id: str,
        media_type: str,
        language: str = "hi",
        timeout_seconds: int = 600,
        metadata: Optional[dict[str, Any]] = None
    ) -> MediaSession:
        """Creates and tracks a new MediaSession."""
        session = MediaSession(
            conversation_id=conversation_id,
            media_type=media_type,
            language=language,
            timeout_seconds=timeout_seconds,
            metadata=metadata or {}
        )
        self._sessions[session.media_session_id] = session
        logger.info(f"Media Session '{session.media_session_id}' started for media '{media_type}'.")

        self._publish_event("media_session_started", session)
        return session

    def get_session(self, media_session_id: str) -> Optional[MediaSession]:
        """Retrieves and touches a media session by ID, marking it expired if timed out."""
        session = self._sessions.get(media_session_id)
        if session:
            if session.is_expired() and session.state == MediaSessionState.ACTIVE:
                session.state = MediaSessionState.EXPIRED
                logger.info(f"Media Session '{media_session_id}' has expired.")
                self._publish_event("media_session_expired", session)
            else:
                session.touch()
        return session

    def recover_session(self, media_session_id: str) -> Optional[MediaSession]:
        """Recovers an expired session, moving it back to RECOVERED/ACTIVE state."""
        session = self._sessions.get(media_session_id)
        if not session:
            return None
        session.state = MediaSessionState.RECOVERED
        session.recovery_count += 1
        session.touch()
        logger.info(f"Media Session '{media_session_id}' successfully recovered (Count: {session.recovery_count}).")
        self._publish_event("media_session_recovered", session)
        return session

    def close_session(self, media_session_id: str) -> None:
        """Closes an active session."""
        session = self._sessions.get(media_session_id)
        if session:
            session.state = MediaSessionState.CLOSED
            logger.info(f"Media Session '{media_session_id}' closed.")
            self._publish_event("media_session_ended", session)

    def cleanup_expired(self) -> int:
        """Runs expiration checks, changing state of timed-out active sessions."""
        count = 0
        for session in self._sessions.values():
            if session.state == MediaSessionState.ACTIVE and session.is_expired():
                session.state = MediaSessionState.EXPIRED
                count += 1
                self._publish_event("media_session_expired", session)
        return count

    def list_sessions(self) -> list[MediaSession]:
        return list(self._sessions.values())

    def _publish_event(self, event_type: str, session: MediaSession) -> None:
        if self._event_bus:
            try:
                from app.core.event_bus import Event
                self._event_bus.publish(Event(
                    event_type=event_type,
                    trace_id="media_session",
                    request_id="session_manager",
                    session_id=session.conversation_id,
                    payload={
                        "media_session_id": session.media_session_id,
                        "conversation_id": session.conversation_id,
                        "media_type": session.media_type,
                        "state": session.state.value
                    }
                ))
            except Exception as e:
                logger.error(f"Failed to publish event '{event_type}': {e}")
