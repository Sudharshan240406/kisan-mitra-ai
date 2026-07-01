from enum import Enum


class TelephonyEventType(str, Enum):
    """Telephony and IVR lifecycle event types published to platform EventBus."""
    INCOMING_CALL = "telephony_incoming_call"
    CALL_ANSWERED = "telephony_call_answered"
    IVR_STARTED = "telephony_ivr_started"
    LANGUAGE_SELECTED = "telephony_language_selected"
    RECOMMENDATION_PLAYED = "telephony_recommendation_played"
    DTMF_RECEIVED = "telephony_dtmf_received"
    CALL_ENDED = "telephony_call_ended"
    CALL_DROPPED = "telephony_call_dropped"
    CALL_TRANSFERRED = "telephony_call_transferred"
