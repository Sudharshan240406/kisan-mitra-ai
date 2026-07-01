from enum import Enum


class MediaEventType(str, Enum):
    """MIP framework lifecycle event types published to platform EventBus."""
    MEDIA_RECEIVED = "media_received"
    MEDIA_VALIDATED = "media_validated"
    MEDIA_PROCESSED = "media_processed"
    MEDIA_REJECTED = "media_rejected"
    MEDIA_SESSION_STARTED = "media_session_started"
    MEDIA_SESSION_ENDED = "media_session_ended"
    PROCESSING_COMPLETED = "processing_completed"
    PROCESSING_FAILED = "processing_failed"
