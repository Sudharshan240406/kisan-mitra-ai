"""
Channel lifecycle event definitions integrated with the platform EventBus.
"""
from enum import Enum


class ChannelEventType(str, Enum):
    """Standard channel lifecycle event type codes."""
    CHANNEL_CONNECTED = "channel_connected"
    CHANNEL_DISCONNECTED = "channel_disconnected"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_PROCESSED = "message_processed"
    RESPONSE_GENERATED = "response_generated"
    RESPONSE_DELIVERED = "response_delivered"
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    SESSION_EXPIRED = "session_expired"
    SESSION_RECOVERED = "session_recovered"
    ERROR_OCCURRED = "error_occurred"
    CHANNEL_HEALTH_CHECK = "channel_health_check"
