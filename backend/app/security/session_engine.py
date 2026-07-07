import time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SessionRecord(BaseModel):
    session_id: str
    user_id: str
    token: str
    login_time: float = Field(default_factory=time.time)
    last_active: float = Field(default_factory=time.time)
    is_active: bool = True

class SessionEngine:
    """
    In-memory session manager tracking login, logout, idle timeout, and concurrent session limits.
    """
    def __init__(self) -> None:
        self._sessions: Dict[str, SessionRecord] = {}

    def create_session(self, user_id: str, token: str, max_concurrent: int = 3) -> str:
        """
        Creates a new session record. If the concurrent sessions limit is exceeded,
        invalidates the oldest active session.
        """
        # 1. Enforce concurrent sessions cap
        active_user_sessions = [
            s for s in self._sessions.values()
            if s.user_id == user_id and s.is_active
        ]

        if len(active_user_sessions) >= max_concurrent:
            # Sort by login time (oldest first)
            active_user_sessions.sort(key=lambda x: x.login_time)
            # Invalidate oldest
            oldest = active_user_sessions[0]
            oldest.is_active = False
            # Clean from storage or mark inactive
            self.invalidate_session(oldest.session_id)

        # 2. Allocate new session
        # Use token signature hash or generate a unique ID
        session_id = f"sess_{hashlib_sha256_short(token)}"
        record = SessionRecord(
            session_id=session_id,
            user_id=user_id,
            token=token
        )
        self._sessions[session_id] = record
        return session_id

    def invalidate_session(self, session_id: str) -> None:
        """
        Invalidates a session (explicit logout).
        """
        if session_id in self._sessions:
            self._sessions[session_id].is_active = False

    def touch_session(self, session_id: str, timeout_seconds: int = 1800) -> bool:
        """
        Touches the session to update last active timestamp.
        Returns False if the session has expired or is inactive.
        """
        if session_id not in self._sessions:
            return False

        record = self._sessions[session_id]
        if not record.is_active:
            return False

        current_time = time.time()
        # Check idle timeout limit
        if current_time - record.last_active > timeout_seconds:
            record.is_active = False
            return False

        record.last_active = current_time
        return True

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        """
        Retrieves session context by ID.
        """
        return self._sessions.get(session_id)

    def get_active_sessions(self, user_id: Optional[str] = None) -> List[SessionRecord]:
        """
        Retrieves active sessions list, optionally filtered by user ID.
        """
        return [
            s for s in self._sessions.values()
            if s.is_active and (user_id is None or s.user_id == user_id)
        ]

    def cleanup_expired_sessions(self, timeout_seconds: int = 1800) -> None:
        """
        Periodically checks and invalidates idle expired sessions.
        """
        current_time = time.time()
        for session in list(self._sessions.values()):
            if session.is_active and (current_time - session.last_active > timeout_seconds):
                session.is_active = False

    def clear(self) -> None:
        """Resets all session records."""
        self._sessions.clear()

def hashlib_sha256_short(data: str) -> str:
    """Helper to generate a short unique string from token."""
    import hashlib
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]
