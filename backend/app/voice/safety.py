"""
Kisan Mitra AI — Voice Safety Engine
=======================================
Detects and handles safety-critical situations during voice calls:
  - Emergency situations (crop failure, financial distress)
  - Repeated STT failures (low confidence threshold)
  - Repeated off-topic or abusive inputs
  - Low overall reasoning confidence
  - Human escalation triggers

Returns EscalationDecision for the CallManager to act on.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.voice.session import VoiceSession

logger = logging.getLogger("kisan_mitra_ai.voice.safety")


# ---------------------------------------------------------------------------
# Safety Signal Keywords (multilingual)
# ---------------------------------------------------------------------------

EMERGENCY_KEYWORDS: frozenset[str] = frozenset([
    # Hindi
    "मदद", "आपातकाल", "संकट", "बर्बाद", "नुकसान", "कर्ज", "आत्महत्या",
    "बीमार", "अस्पताल",
    # English
    "emergency", "help", "crisis", "loss", "debt", "bankrupt", "suicide",
    "hospital", "flood", "fire", "disaster",
    # Kannada
    "ಸಹಾಯ", "ಅಪಾಯ", "ಸಂಕಟ", "ನಷ್ಟ", "ಆತ್ಮಹತ್ಯೆ",
    # Telugu
    "సహాయం", "అత్యవసరం", "నష్టం", "ఆత్మహత్య",
    # Tamil
    "உதவி", "ஆபத்து", "இழப்பு",
])

ABUSE_KEYWORDS: frozenset[str] = frozenset([
    "stupid", "idiot", "useless", "cheat", "fraud", "scam",
    "बेकार", "बेवकूफ", "धोखा", "ठगी",
])

OFF_TOPIC_KEYWORDS: frozenset[str] = frozenset([
    "movie", "cricket", "politics", "film", "song", "गाना", "क्रिकेट",
    "ਫਿਲਮ", "ਕ੍ਰਿਕੇਟ",
])


# ---------------------------------------------------------------------------
# EscalationDecision
# ---------------------------------------------------------------------------

class EscalationDecision(BaseModel):
    """Output of the safety engine evaluation."""
    escalate: bool = False
    reason: str = ""
    priority: str = "normal"   # normal | urgent | emergency
    route_to: str = "KVK_EXPERT_QUEUE"
    flags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# VoiceSafetyEngine
# ---------------------------------------------------------------------------

class VoiceSafetyEngine:
    """
    Evaluates voice sessions for safety-critical conditions.
    Triggered after every turn and on session close.

    Priority order (first match wins):
      1. Emergency keywords → emergency escalation
      2. Repeated STT failures → urgent escalation
      3. Low reasoning confidence → normal escalation
      4. Off-topic or abusive input → polite redirect / escalation
    """

    def __init__(
        self,
        confidence_threshold: float = 0.30,
        max_stt_failures: int = 3,
        max_off_topic: int = 2,
        max_abuse: int = 1,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.max_stt_failures = max_stt_failures
        self.max_off_topic = max_off_topic
        self.max_abuse = max_abuse

        self._off_topic_count: dict[str, int] = {}
        self._abuse_count: dict[str, int] = {}
        self.total_escalations: int = 0

    def evaluate(
        self,
        session: VoiceSession,
        transcript: str,
        stt_confidence: float,
        reasoning_confidence: float,
    ) -> EscalationDecision:
        """
        Evaluate all safety signals for the current turn.
        Returns EscalationDecision.
        """
        call_id = session.call_id
        text = transcript.lower()
        flags: list[str] = []

        # 1. Emergency keyword detection
        for kw in EMERGENCY_KEYWORDS:
            if kw.lower() in text:
                flags.append(f"EMERGENCY_KEYWORD:{kw}")
                self.total_escalations += 1
                session.safety_flags.append(f"EMERGENCY:{kw}")
                return EscalationDecision(
                    escalate=True,
                    reason=f"Emergency keyword detected: '{kw}'",
                    priority="emergency",
                    route_to="EMERGENCY_AGRICULTURAL_HELPLINE",
                    flags=flags,
                )

        # 2. Abuse detection
        abuse_count = self._abuse_count.get(call_id, 0)
        for kw in ABUSE_KEYWORDS:
            if kw.lower() in text:
                abuse_count += 1
                flags.append(f"ABUSE:{kw}")
                break
        self._abuse_count[call_id] = abuse_count
        if abuse_count >= self.max_abuse:
            self.total_escalations += 1
            return EscalationDecision(
                escalate=True,
                reason="Repeated abusive input detected.",
                priority="urgent",
                route_to="KVK_EXPERT_QUEUE",
                flags=flags,
            )

        # 3. Off-topic detection
        off_topic_count = self._off_topic_count.get(call_id, 0)
        for kw in OFF_TOPIC_KEYWORDS:
            if kw.lower() in text:
                off_topic_count += 1
                flags.append(f"OFF_TOPIC:{kw}")
                break
        self._off_topic_count[call_id] = off_topic_count

        # 4. STT failure check
        if stt_confidence < 0.35:
            session.consecutive_failures += 1
        else:
            session.consecutive_failures = 0

        if session.consecutive_failures >= self.max_stt_failures:
            self.total_escalations += 1
            return EscalationDecision(
                escalate=True,
                reason=f"Repeated STT failures ({session.consecutive_failures}).",
                priority="urgent",
                route_to="KVK_EXPERT_QUEUE",
                flags=flags,
            )

        # 5. Low reasoning confidence
        if reasoning_confidence < self.confidence_threshold and reasoning_confidence > 0:
            self.total_escalations += 1
            return EscalationDecision(
                escalate=True,
                reason=f"Low reasoning confidence: {reasoning_confidence:.2f}",
                priority="normal",
                route_to="KVK_EXPERT_QUEUE",
                flags=flags,
            )

        return EscalationDecision(escalate=False, flags=flags)

    def evaluate_session_close(self, session: VoiceSession) -> Optional[EscalationDecision]:
        """
        Final safety check on session close.
        Escalates if session ended with zero recommendations.
        """
        if not session.recommendations_given and session.turn_count > 2:
            return EscalationDecision(
                escalate=True,
                reason="Session ended without any recommendation delivered.",
                priority="normal",
                route_to="KVK_EXPERT_QUEUE",
            )
        return None

    def get_safe_redirect(self, language: str) -> str:
        msgs = {
            "hi": "मैं आपकी इस समस्या में मदद नहीं कर सकता। कृपया किसान हेल्पलाइन 1800-180-1551 पर कॉल करें।",
            "en": "I cannot help with this. Please call the Kisan Helpline at 1800-180-1551.",
            "kn": "ನಾನು ಈ ವಿಷಯದಲ್ಲಿ ಸಹಾಯ ಮಾಡಲಾಗುವುದಿಲ್ಲ. ದಯವಿಟ್ಟು 1800-180-1551 ಗೆ ಕರೆ ಮಾಡಿ.",
            "te": "ఈ విషయంలో నేను సహాయం చేయలేను. దయచేసి 1800-180-1551 కి కాల్ చేయండి.",
        }
        return msgs.get(language, msgs["hi"])

    def stats(self) -> dict[str, Any]:
        return {"total_escalations": self.total_escalations}
