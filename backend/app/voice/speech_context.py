"""
Kisan Mitra AI — Speech Context
==================================
Manages per-call conversation context, farmer profile loading,
conversation state history, session resumption, and intent tracking.

The SpeechContext is the intelligence layer bridging raw transcripts
to structured agricultural advisory requests.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.voice.session import FarmerProfileSnapshot, VoiceSession

logger = logging.getLogger("kisan_mitra_ai.voice.speech_context")


# ---------------------------------------------------------------------------
# Intent
# ---------------------------------------------------------------------------

class VoiceIntent(BaseModel):
    """Recognized intent from a farmer's transcript."""
    intent_type: str = Field(..., description="Intent category: weather/market/disease/scheme/general")
    entities: dict[str, str] = Field(default_factory=dict)
    crop: Optional[str] = None
    location: Optional[str] = None
    raw_query: str = ""
    confidence: float = 0.0


# ---------------------------------------------------------------------------
# Intent Extraction (rule-based, no LLM dependency)
# ---------------------------------------------------------------------------

_INTENT_RULES: list[tuple[frozenset[str], str]] = [
    (frozenset(["मौसम", "बारिश", "weather", "rain", "ಮಳೆ", "వర్షం", "மழை"]), "weather"),
    (frozenset(["बाजार", "भाव", "market", "price", "mandi", "ಮಾರ್ಕೆಟ್", "మార్కెట్"]), "market"),
    (frozenset(["रोग", "कीड़े", "disease", "pest", "fungus", "ರೋಗ", "రోగం", "நோய்"]), "disease"),
    (frozenset(["योजना", "scheme", "subsidy", "government", "ಯೋಜನೆ", "పథకం"]), "scheme"),
    (frozenset(["खाद", "fertilizer", "urea", "dap", "potash", "ಗೊಬ್ಬರ", "ఎరువు"]), "fertilizer"),
    (frozenset(["सिंचाई", "irrigation", "water", "pump", "ನೀರಾವರಿ", "నీరు"]), "irrigation"),
    (frozenset(["बुवाई", "sowing", "seed", "planting", "ಬಿತ್ತನೆ", "విత్తనాలు"]), "sowing"),
]

_CROP_KEYWORDS: dict[str, list[str]] = {
    "wheat": ["गेहूं", "wheat", "ಗೋಧಿ", "గోధుమ", "கோதுமை"],
    "rice": ["धान", "चावल", "rice", "ಅಕ್ಕಿ", "వరి", "அரிசி"],
    "cotton": ["कपास", "cotton", "ಹತ್ತಿ", "పత్తి", "பருத்தி"],
    "sugarcane": ["गन्ना", "sugarcane", "ಕಬ್ಬು", "చెరకు", "கரும்பு"],
    "maize": ["मक्का", "corn", "maize", "ಮೆಕ್ಕೆಜೋಳ", "మొక్కజొన్న"],
    "soybean": ["सोयाबीन", "soybean", "ಸೋಯಾ", "సోయా"],
    "groundnut": ["मूंगफली", "groundnut", "peanut", "ಕಡಲೆ", "వేరుశనగ"],
    "tomato": ["टमाटर", "tomato", "ಟೊಮೇಟೊ", "టమాటా", "தக்காளி"],
}


def extract_intent(transcript: str, language: str = "hi") -> VoiceIntent:
    """
    Rule-based intent extraction from farmer transcript.
    No LLM calls — deterministic, low latency.
    """
    text = transcript.lower()
    matched_intent = "general"
    intent_confidence = 0.5

    for keywords, intent_type in _INTENT_RULES:
        for kw in keywords:
            if kw.lower() in text:
                matched_intent = intent_type
                intent_confidence = 0.80
                break

    # Crop detection
    detected_crop: Optional[str] = None
    for crop, keywords in _CROP_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text:
                detected_crop = crop
                break

    return VoiceIntent(
        intent_type=matched_intent,
        raw_query=transcript,
        confidence=intent_confidence,
        crop=detected_crop,
        entities={"crop": detected_crop or ""} if detected_crop else {},
    )


# ---------------------------------------------------------------------------
# SpeechContext
# ---------------------------------------------------------------------------

class SpeechContext:
    """
    Per-call conversation context manager.

    Responsibilities:
      - Load farmer profile at call start
      - Track conversation history for continuity
      - Maintain session resumption state
      - Extract and cache intents
      - Detect topic changes
      - Handle clarification state
    """

    def __init__(self, session: VoiceSession) -> None:
        self.session = session
        self._intent_history: list[VoiceIntent] = []
        self._last_advisory: str = ""
        self._topic_change_detected: bool = False

    def load_profile(self, profile: FarmerProfileSnapshot) -> None:
        """Load farmer profile at call start."""
        self.session.farmer_profile = profile
        if profile.preferred_language and not self.session.language_locked:
            self.session.detected_language = profile.preferred_language
        logger.info(
            f"[SpeechContext] Loaded profile for farmer '{profile.farmer_id}', "
            f"language='{profile.preferred_language}', crops={profile.crops}"
        )

    def process_transcript(self, transcript: str) -> VoiceIntent:
        """
        Process a farmer transcript: extract intent, detect topic change.
        """
        intent = extract_intent(transcript, self.session.detected_language)

        # Check for topic change
        if self._intent_history:
            last = self._intent_history[-1]
            self._topic_change_detected = (last.intent_type != intent.intent_type)

        self._intent_history.append(intent)
        self.session.current_intent = intent.intent_type

        # Enrich with profile context
        if not intent.crop and self.session.farmer_profile.crops:
            intent.crop = self.session.farmer_profile.crops[0]
            intent.entities["crop"] = intent.crop

        if not intent.location:
            intent.location = self.session.farmer_profile.location

        logger.debug(f"[SpeechContext] Intent: {intent.intent_type}, crop={intent.crop}")
        return intent

    def build_advisory_query(self, intent: VoiceIntent) -> str:
        """
        Constructs a structured query string for the reasoning pipeline
        from the intent + session context.
        """
        parts = []

        if intent.crop:
            parts.append(f"crop: {intent.crop}")
        if intent.location or self.session.farmer_profile.location:
            loc = intent.location or self.session.farmer_profile.location
            parts.append(f"location: {loc}")
        if self.session.farmer_profile.season:
            parts.append(f"season: {self.session.farmer_profile.season}")

        context = ", ".join(parts)
        query = intent.raw_query
        if context:
            query = f"{query} [{context}]"
        return query

    def get_greeting(self) -> str:
        """Personalized greeting using farmer profile."""
        profile = self.session.farmer_profile
        if profile.name:
            if self.session.detected_language == "hi":
                return f"नमस्ते {profile.name} जी,"
            elif self.session.detected_language == "kn":
                return f"ನಮಸ್ಕಾರ {profile.name},"
            elif self.session.detected_language == "te":
                return f"నమస్కారం {profile.name},"
            elif self.session.detected_language == "ta":
                return f"வணக்கம் {profile.name},"
            else:
                return f"Hello {profile.name},"
        return "नमस्ते," if self.session.detected_language == "hi" else "Hello,"

    def store_advisory(self, advisory_text: str) -> None:
        """Records advisory in session for Digital Twin."""
        self._last_advisory = advisory_text
        self.session.recommendations_given.append(advisory_text[:200])  # truncated

    def get_clarification_prompt(self) -> str:
        """Returns language-appropriate clarification prompt."""
        lang = self.session.detected_language
        prompts = {
            "hi": "कृपया अपना प्रश्न दोबारा बताएं।",
            "kn": "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆ ಮತ್ತೆ ಹೇಳಿ.",
            "te": "దయచేసి మీ ప్రశ్న మళ్లీ చెప్పండి.",
            "ta": "உங்கள் கேள்வியை மீண்டும் சொல்லுங்கள்.",
            "en": "Please repeat your question.",
            "pa": "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ ਸਵਾਲ ਦੁਬਾਰਾ ਦੱਸੋ।",
        }
        return prompts.get(lang, prompts["hi"])

    def summary(self) -> dict[str, Any]:
        return {
            "session_id": self.session.session_id,
            "language": self.session.detected_language,
            "intents": [i.intent_type for i in self._intent_history],
            "topic_changed": self._topic_change_detected,
            "turn_count": self.session.turn_count,
            "last_advisory_len": len(self._last_advisory),
        }
