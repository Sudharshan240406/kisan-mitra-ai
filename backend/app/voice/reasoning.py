"""
Kisan Mitra AI — Voice Reasoning Pipeline
==========================================
Connects the Speech layer to the full AI reasoning stack.

Pipeline:
  STTResult (transcript)
    ↓
  SpeechContext.process_transcript() → VoiceIntent
    ↓
  Build advisory query
    ↓
  ChiefReasoningAgent.reason() (via container)
    ↓
  ReasoningResult → advisory text
    ↓
  ConversationManager.deliver_response()
    ↓
  TTS synthesis

The VoiceReasoningPipeline is the bridge between audio and intelligence.
It reuses the existing ChiefReasoningAgent — no duplication of reasoning logic.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from pydantic import BaseModel, Field

from app.voice.session import VoiceSession
from app.voice.speech_context import SpeechContext, VoiceIntent

logger = logging.getLogger("kisan_mitra_ai.voice.reasoning")


class VoiceReasoningResult(BaseModel):
    """Standardized output from the voice reasoning pipeline."""
    advisory_text: str = Field(..., description="Human-readable advisory text for TTS.")
    confidence: float = Field(..., description="Overall reasoning confidence.")
    latency_ms: float = Field(default=0.0)
    escalated: bool = Field(default=False)
    escalation_reason: Optional[str] = None
    intent_type: str = "general"
    weather_consulted: bool = False
    market_consulted: bool = False
    schemes_discussed: list[str] = Field(default_factory=list)
    follow_up_reminders: list[str] = Field(default_factory=list)
    reasoning_path: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VoiceReasoningPipeline:
    """
    Bridges voice transcripts to the ChiefReasoningAgent.

    Design principles:
      - Reuses the existing reasoning infrastructure (no redesign).
      - Routes through channel_router (omnichannel) when chief_agent
        is not directly injectable (fallback path).
      - Wraps output in VoiceReasoningResult for the TTS layer.
    """

    def __init__(self, container: Any) -> None:
        self._container = container

    async def reason(
        self,
        transcript: str,
        intent: VoiceIntent,
        session: VoiceSession,
        context: SpeechContext,
    ) -> VoiceReasoningResult:
        """
        Execute the full reasoning pipeline for a voice query.
        Returns VoiceReasoningResult with advisory text + metadata.
        """
        start = time.perf_counter()
        query = context.build_advisory_query(intent)
        language = session.detected_language

        logger.info(
            f"[VoiceReasoning] call={session.call_id} intent={intent.intent_type} "
            f"query='{query[:80]}' lang={language}"
        )

        advisory_text = ""
        confidence = 0.6
        escalated = False
        escalation_reason: Optional[str] = None
        weather_consulted = intent.intent_type == "weather"
        market_consulted = intent.intent_type == "market"

        try:
            # Primary path: ChiefReasoningAgent (Step 10C)
            if hasattr(self._container, "chief_agent"):
                result = await self._container.chief_agent.reason(
                    query=query,
                    trace_id=session.trace_id or f"voice-{session.call_id}",
                    request_id=f"voice-{session.call_id}",
                    parsed_evidence=[],
                    missing_fields=[
                        field_name
                        for field_name, value in {
                            "crop": intent.crop,
                            "location": intent.location or session.farmer_profile.location,
                        }.items()
                        if not value
                    ],
                    language=language,
                    crop=intent.crop,
                    location=intent.location or session.farmer_profile.location,
                )
                advisory_text = result.primary_recommendation
                confidence = result.overall_confidence
                escalated = result.escalated
                escalation_reason = result.escalation_reason
                session.weather_consulted = weather_consulted
                session.market_consulted = market_consulted
                session.schemes_discussed = result.suggested_actions[:2] if intent.intent_type == "scheme" else []
                session.follow_up_reminders = result.suggested_actions

            # Fallback path: channel_router (existing omnichannel pipeline)
            elif hasattr(self._container, "channel_router"):
                from app.channels.envelope import LanguageMetadata, MessageEnvelope, MessagePriority

                lang_meta = LanguageMetadata(preferred_language=language, locale=language)
                envelope = MessageEnvelope(
                    conversation_id=session.session_id,
                    channel="voice-001",
                    sender=session.caller_number or "voice-farmer",
                    receiver="system",
                    language=lang_meta,
                    payload={"text": query},
                    priority=MessagePriority.HIGH,
                    trace_id=session.trace_id,
                )
                response = await self._container.channel_router.route_inbound(envelope, asynchronous=False)
                if response and response.payload:
                    advisory_text = (
                        response.payload.get("recommendation")
                        or response.payload.get("text")
                        or ""
                    )
                    confidence = float(response.payload.get("confidence", 0.6))

            if not advisory_text:
                advisory_text = self._fallback_response(intent.intent_type, language)
                confidence = 0.4

        except Exception as exc:
            logger.error(f"[VoiceReasoning] Pipeline error: {exc}", exc_info=True)
            advisory_text = self._error_response(language)
            confidence = 0.0

        latency_ms = round((time.perf_counter() - start) * 1000, 2)

        return VoiceReasoningResult(
            advisory_text=advisory_text,
            confidence=confidence,
            latency_ms=latency_ms,
            escalated=escalated,
            escalation_reason=escalation_reason,
            intent_type=intent.intent_type,
            weather_consulted=weather_consulted,
            market_consulted=market_consulted,
            follow_up_reminders=session.follow_up_reminders,
            reasoning_path=getattr(locals().get("result", None), "reasoning_path", []),
            metadata={
                "session_id": session.session_id,
                "trace_id": session.trace_id,
                "language": language,
            },
        )

    def _fallback_response(self, intent_type: str, language: str) -> str:
        """Returns a safe fallback response if reasoning fails."""
        msgs: dict[str, dict[str, str]] = {
            "hi": {
                "weather": "आपके क्षेत्र के मौसम की जानकारी अभी उपलब्ध नहीं है।",
                "market": "बाजार भाव अभी उपलब्ध नहीं है। कृपया बाद में प्रयास करें।",
                "general": "आपके प्रश्न का उत्तर अभी उपलब्ध नहीं है। कृपया KVK हेल्पलाइन से संपर्क करें।",
            },
            "en": {
                "weather": "Weather information is currently unavailable.",
                "market": "Market prices are currently unavailable.",
                "general": "Advisory not available. Please contact your KVK helpline.",
            },
        }
        lang_msgs = msgs.get(language, msgs["hi"])
        return lang_msgs.get(intent_type, lang_msgs["general"])

    def _error_response(self, language: str) -> str:
        msgs = {
            "hi": "तकनीकी समस्या के कारण सलाह उपलब्ध नहीं है। कृपया पुनः प्रयास करें।",
            "en": "Technical error. Advisory unavailable. Please try again.",
            "kn": "ತಾಂತ್ರಿಕ ದೋಷ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
            "te": "సాంకేతిక లోపం. దయచేసి మళ్లీ ప్రయత్నించండి.",
        }
        return msgs.get(language, msgs["hi"])
