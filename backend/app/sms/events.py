from enum import Enum


class SMSEventType(str, Enum):
    """SMS platform lifecycle event types published to platform EventBus."""
    SMS_RECEIVED = "sms_received"
    SMS_SENT = "sms_sent"
    SMS_DELIVERED = "sms_delivered"
    SMS_FAILED = "sms_failed"
    SMS_RETRY = "sms_retry"
    SESSION_STARTED = "sms_session_started"
    SESSION_ENDED = "sms_session_ended"
    TEMPLATE_RENDERED = "sms_template_rendered"
