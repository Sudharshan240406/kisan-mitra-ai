import logging
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Using the pre-configured security logger
logger = logging.getLogger("kisan_mitra_ai.security.audit")

class AuditEvent(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    event_type: str  # auth, authz, role_change, permission_change, sensitive_api
    user_id: str
    action: str
    status: str      # success, failure
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AuditEngine:
    """
    Core security auditing engine writing structured logs to the audit handler
    and maintaining a rolling in-memory buffer of recent events.
    """
    def __init__(self, max_buffer_size: int = 100) -> None:
        self.max_buffer_size = max_buffer_size
        self._buffer: List[AuditEvent] = []

    def log_audit(
        self,
        event_type: str,
        user_id: str,
        action: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """
        Records an audit event, logs it to the security log channel, and buffers it.
        """
        meta = metadata or {}
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            action=action,
            status=status,
            metadata=meta
        )

        # Buffer log event
        self._buffer.append(event)
        if len(self._buffer) > self.max_buffer_size:
            self._buffer.pop(0)

        # Format for output files
        log_message = (
            f"[AUDIT] type={event_type} | user={user_id} | action={action} | "
            f"status={status} | meta={meta}"
        )

        if status == "failure":
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return event

    def get_events(self, limit: int = 50) -> List[AuditEvent]:
        """
        Returns recent audit log events sorted descending by timestamp.
        """
        sorted_events = sorted(self._buffer, key=lambda x: x.timestamp, reverse=True)
        return sorted_events[:limit]

    def clear(self) -> None:
        """Resets the audit buffer."""
        self._buffer.clear()
