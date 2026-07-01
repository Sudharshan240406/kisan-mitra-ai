"""
Kisan Mitra AI — Conversation Manager
========================================
Manages the full voice conversation lifecycle:
  1. Greeting
  2. Identity verification (phone number lookup)
  3. Context loading (profile + history)
  4. Main conversation loop
  5. Clarification handling
  6. Closing / session teardown
  7. Session timeout detection
  8. Resume previous session
"""
from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.voice.session import TranscriptTurn, VoiceSession

logger = logging.getLogger("kisan_mitra_ai.voice.conversation")


class ConversationStage(str, Enum):
    GREETING = "GREETING"
    IDENTITY = "IDENTITY"
    CONTEXT_LOADING = "CONTEXT_LOADING"
    LISTENING = "LISTENING"
    CLARIFICATION = "CLARIFICATION"
    RESPONDING = "RESPONDING"
    CONFIRMATION = "CONFIRMATION"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"


class ConversationTurn(BaseModel):
    stage: str
    farmer_text: str = ""
    assistant_text: str = ""
    intent: str = ""
    confidence: float = 0.0
    latency_ms: float = 0.0
    timestamp: float = Field(default_factory=time.time)


class ConversationManager:
    """
    Orchestrates the voice conversation lifecycle for a VoiceSession.
    Stateful: one ConversationManager per active call.
    """

    GREETING_TEXTS: dict[str, str] = {
        "hi": "किसान मित्र में आपका स्वागत है। मैं आपकी खेती से जुड़ी समस्याओं में मदद करूंगा।",
        "en": "Welcome to Kisan Mitra. I am here to help with your farming queries.",
        "kn": "ಕಿಸಾನ್ ಮಿತ್ರಕ್ಕೆ ಸ್ವಾಗತ. ನಿಮ್ಮ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳಿಗೆ ನಾನು ಸಹಾಯ ಮಾಡುತ್ತೇನೆ.",
        "te": "కిసాన్ మిత్రకు స్వాగతం. మీ వ్యవసాయ ప్రశ్నలకు నేను సహాయం చేస్తాను.",
        "ta": "கிசான் மித்ராவிற்கு வரவேற்கிறோம். உங்கள் விவசாய கேள்விகளுக்கு உதவுகிறேன்.",
        "pa": "ਕਿਸਾਨ ਮਿੱਤਰ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ। ਮੈਂ ਤੁਹਾਡੀਆਂ ਖੇਤੀਬਾੜੀ ਸਮੱਸਿਆਵਾਂ ਵਿੱਚ ਮਦਦ ਕਰਾਂਗਾ।",
        "mr": "किसान मित्रमध्ये आपले स्वागत आहे. मी आपल्या शेती प्रश्नांमध्ये मदत करेन.",
    }

    CLOSING_TEXTS: dict[str, str] = {
        "hi": "किसान मित्र से संपर्क करने के लिए धन्यवाद। आपकी फसल लहलहाए!",
        "en": "Thank you for calling Kisan Mitra. Have a great harvest!",
        "kn": "ಕಿಸಾನ್ ಮಿತ್ರಕ್ಕೆ ಕರೆ ಮಾಡಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದ. ಉತ್ತಮ ಬೆಳೆ ಬೆಳೆಯಿರಿ!",
        "te": "కిసాన్ మిత్రకు కాల్ చేసినందుకు ధన్యవాదాలు. మంచి పంట పండించండి!",
        "ta": "கிசான் மித்ராவை அழைத்தத்திற்கு நன்றி. நல்ல விளைச்சல் பெறுங்கள்!",
        "pa": "ਕਿਸਾਨ ਮਿੱਤਰ ਨਾਲ ਸੰਪਰਕ ਕਰਨ ਲਈ ਧੰਨਵਾਦ। ਚੰਗੀ ਫਸਲ ਹੋਵੇ!",
    }

    TIMEOUT_WARNING: dict[str, str] = {
        "hi": "क्या आप अभी भी लाइन पर हैं? कृपया बोलें।",
        "en": "Are you still there? Please speak.",
        "kn": "ನೀವು ಇನ್ನೂ ಕಾಲ್‌ನಲ್ಲಿ ಇದ್ದೀರಾ?",
        "te": "మీరు ఇంకా ఆన్ లైన్‌లో ఉన్నారా?",
    }

    def __init__(
        self,
        session: VoiceSession,
        timeout_seconds: float = 300.0,
        clarification_limit: int = 3,
    ) -> None:
        self.session = session
        self.timeout_seconds = timeout_seconds
        self.clarification_limit = clarification_limit
        self._stage = ConversationStage.GREETING
        self._history: list[ConversationTurn] = []
        self._last_activity = time.time()
        self._previous_advisory: str = ""

    @property
    def stage(self) -> ConversationStage:
        return self._stage

    def greet(self, farmer_name: Optional[str] = None) -> str:
        lang = self.session.detected_language
        base = self.GREETING_TEXTS.get(lang, self.GREETING_TEXTS["hi"])
        if farmer_name:
            if lang == "hi":
                greeting = f"नमस्ते {farmer_name} जी! {base}"
            else:
                greeting = f"Hello {farmer_name}! {base}"
        else:
            greeting = base

        # Check for previous session resumption
        if self.session.farmer_profile.last_call_id:
            if lang == "hi":
                greeting += " पिछली बार की आपकी बात याद है मुझे।"
            else:
                greeting += " I remember our previous conversation."

        self._stage = ConversationStage.LISTENING
        self._record_assistant_turn(greeting)
        self._touch_activity()
        return greeting

    def handle_timeout_check(self) -> Optional[str]:
        """Returns a timeout warning if silence detected, None otherwise."""
        if time.time() - self._last_activity > self.timeout_seconds * 0.6:
            lang = self.session.detected_language
            return self.TIMEOUT_WARNING.get(lang, self.TIMEOUT_WARNING["en"])
        return None

    def accept_transcript(self, transcript: str, confidence: float, latency_ms: float) -> None:
        """Records a farmer turn to history."""
        turn = TranscriptTurn(
            role="farmer",
            text=transcript,
            language=self.session.detected_language,
            confidence=confidence,
            latency_ms=latency_ms,
        )
        self.session.add_turn(turn)
        self._history.append(ConversationTurn(
            stage=self._stage.value,
            farmer_text=transcript,
            confidence=confidence,
            latency_ms=latency_ms,
        ))
        self._touch_activity()
        self._stage = ConversationStage.RESPONDING

    def deliver_response(self, advisory_text: str, confidence: float, latency_ms: float) -> None:
        """Records an assistant advisory turn."""
        turn = TranscriptTurn(
            role="assistant",
            text=advisory_text,
            language=self.session.detected_language,
            confidence=confidence,
            latency_ms=latency_ms,
        )
        self.session.add_turn(turn)
        if self._history:
            self._history[-1].assistant_text = advisory_text
        self._previous_advisory = advisory_text
        self.session.record_reasoning(confidence, latency_ms)
        self._stage = ConversationStage.CONFIRMATION
        self._touch_activity()

    def request_clarification(self) -> str:
        """Returns a clarification prompt and updates stage."""
        self.session.clarification_attempts += 1
        self._stage = ConversationStage.CLARIFICATION
        if self.session.clarification_attempts >= self.clarification_limit:
            # Escalate after max attempts
            return self._escalation_prompt()
        return self.session.pending_clarification or self._default_clarification()

    def close(self) -> str:
        """Generates closing message and marks session complete."""
        lang = self.session.detected_language
        msg = self.CLOSING_TEXTS.get(lang, self.CLOSING_TEXTS["hi"])
        self.session.complete()
        self._stage = ConversationStage.CLOSED
        self._record_assistant_turn(msg)
        return msg

    def repeat_advisory(self) -> str:
        """Returns the last advisory for repeat playback."""
        return self._previous_advisory or ""

    def get_history(self) -> list[dict[str, Any]]:
        return [t.model_dump() for t in self._history]

    def is_timed_out(self) -> bool:
        return (time.time() - self._last_activity) > self.timeout_seconds

    def _touch_activity(self) -> None:
        self._last_activity = time.time()

    def _record_assistant_turn(self, text: str) -> None:
        turn = TranscriptTurn(role="assistant", text=text, language=self.session.detected_language)
        self.session.add_turn(turn)

    def _default_clarification(self) -> str:
        lang = self.session.detected_language
        msgs = {
            "hi": "क्षमा करें, मैं समझ नहीं पाया। कृपया अपना प्रश्न दोबारा बताएं।",
            "en": "Sorry, I didn't understand. Could you please repeat your question?",
            "kn": "ಕ್ಷಮಿಸಿ, ನನಗೆ ಅರ್ಥವಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಹೇಳಿ.",
            "te": "క్షమించండి, అర్థం కాలేదు. దయచేసి మళ్లీ చెప్పండి.",
            "ta": "மன்னிக்கவும், புரியவில்லை. மீண்டும் கேட்கவும்.",
        }
        return msgs.get(lang, msgs["hi"])

    def _escalation_prompt(self) -> str:
        lang = self.session.detected_language
        msgs = {
            "hi": "आपकी समस्या समझने में कठिनाई हो रही है। आपको कृषि विशेषज्ञ से जोड़ रहे हैं।",
            "en": "Having trouble understanding your query. Connecting you to an agricultural expert.",
            "kn": "ನಿಮ್ಮ ಸಮಸ್ಯೆ ಅರ್ಥಮಾಡಿಕೊಳ್ಳಲು ತೊಂದರೆಯಾಗುತ್ತಿದೆ. ತಜ್ಞರಿಗೆ ಸಂಪರ್ಕಿಸುತ್ತಿದ್ದೇವೆ.",
        }
        return msgs.get(lang, msgs["hi"])
