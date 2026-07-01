"""
Kisan Mitra AI — Voice Session
================================
VoiceSession model: per-call state container tracking:
  - Farmer identity and profile snapshot
  - Detected language and confidence
  - Conversation transcript history
  - STT/TTS/reasoning latency accumulators
  - Escalation and safety state
  - Digital twin integration state
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from pydantic import BaseModel, Field


class TranscriptTurn(BaseModel):
    """One turn (farmer speech or AI response) in the conversation."""
    turn_id: str = Field(default_factory=lambda: f"TURN-{uuid.uuid4().hex[:6]}")
    role: str = Field(..., description="'farmer' or 'assistant'")
    text: str = Field(..., description="Transcript or TTS text.")
    language: str = Field(default="hi")
    confidence: float = Field(default=1.0, description="STT or reasoning confidence.")
    timestamp: float = Field(default_factory=time.time)
    latency_ms: float = Field(default=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FarmerProfileSnapshot(BaseModel):
    """Lightweight farmer profile loaded at call start."""
    farmer_id: Optional[str] = None
    name: Optional[str] = None
    preferred_language: str = "hi"
    crops: list[str] = Field(default_factory=list)
    location: Optional[str] = None
    season: Optional[str] = None
    previous_queries: list[str] = Field(default_factory=list)
    previous_recommendations: list[str] = Field(default_factory=list)
    scheme_history: list[str] = Field(default_factory=list)
    last_call_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VoiceSession(BaseModel):
    """
    Per-call voice session. Holds the complete state of an active voice call.
    Created when a call is answered; closed when the call ends.
    Flushed to Digital Twin Memory on close.
    """
    call_id: str = Field(..., description="Unique call identifier.")
    session_id: str = Field(
        default_factory=lambda: f"VS-{uuid.uuid4().hex[:8].upper()}",
        description="Voice session identifier."
    )
    trace_id: str = Field(default="", description="Distributed trace ID.")
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None

    # Farmer identity
    farmer_profile: FarmerProfileSnapshot = Field(default_factory=FarmerProfileSnapshot)
    caller_number: str = ""

    # Language state
    detected_language: str = "hi"
    language_confidence: float = 0.0
    language_locked: bool = False   # True once confirmed by DTMF or detection

    # Conversation
    turns: list[TranscriptTurn] = Field(default_factory=list)
    current_intent: Optional[str] = None
    pending_clarification: Optional[str] = None
    clarification_attempts: int = 0

    # Quality signals
    avg_stt_confidence: float = 0.0
    avg_reasoning_confidence: float = 0.0
    total_stt_latency_ms: float = 0.0
    total_tts_latency_ms: float = 0.0
    total_reasoning_latency_ms: float = 0.0

    # Safety & escalation
    escalated: bool = False
    escalation_reason: Optional[str] = None
    consecutive_failures: int = 0
    safety_flags: list[str] = Field(default_factory=list)

    # Status
    status: str = "active"   # active | completed | dropped | escalated

    # Digital twin integration
    twin_updated: bool = False
    recommendations_given: list[str] = Field(default_factory=list)
    weather_consulted: bool = False
    market_consulted: bool = False
    schemes_discussed: list[str] = Field(default_factory=list)
    follow_up_reminders: list[str] = Field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_turn(self, turn: TranscriptTurn) -> None:
        self.turns.append(turn)
        if turn.role == "farmer":
            n = sum(1 for t in self.turns if t.role == "farmer")
            self.avg_stt_confidence = round(
                (self.avg_stt_confidence * (n - 1) + turn.confidence) / n, 4
            )
            self.total_stt_latency_ms += turn.latency_ms
        else:
            self.total_tts_latency_ms += turn.latency_ms

    def record_reasoning(self, confidence: float, latency_ms: float) -> None:
        n = max(1, sum(1 for t in self.turns if t.role == "assistant"))
        self.avg_reasoning_confidence = round(
            (self.avg_reasoning_confidence * (n - 1) + confidence) / n, 4
        )
        self.total_reasoning_latency_ms += latency_ms

    def complete(self) -> None:
        self.end_time = time.time()
        self.status = "completed"

    def drop(self) -> None:
        self.end_time = time.time()
        self.status = "dropped"

    def escalate(self, reason: str) -> None:
        self.end_time = time.time()
        self.escalated = True
        self.escalation_reason = reason
        self.status = "escalated"
        self.safety_flags.append(f"ESCALATED: {reason}")

    @property
    def duration_seconds(self) -> float:
        end = self.end_time or time.time()
        return round(end - self.start_time, 2)

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    def to_twin_record(self) -> dict[str, Any]:
        """Serializes the session for Digital Twin Memory storage."""
        return {
            "call_id": self.call_id,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "farmer_id": self.farmer_profile.farmer_id,
            "language": self.detected_language,
            "duration_seconds": self.duration_seconds,
            "turns": len(self.turns),
            "status": self.status,
            "escalated": self.escalated,
            "escalation_reason": self.escalation_reason,
            "avg_stt_confidence": self.avg_stt_confidence,
            "avg_reasoning_confidence": self.avg_reasoning_confidence,
            "recommendations_given": self.recommendations_given,
            "weather_consulted": self.weather_consulted,
            "market_consulted": self.market_consulted,
            "schemes_discussed": self.schemes_discussed,
            "follow_up_reminders": self.follow_up_reminders,
            "safety_flags": self.safety_flags,
            "transcript": [t.model_dump() for t in self.turns],
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


class VoiceSessionManager:
    """
    In-memory registry for active voice sessions.
    Mirrors the pattern used by CallSessionManager (telephony layer).
    """

    def __init__(self, timeout_seconds: float = 300.0) -> None:
        self._sessions: dict[str, VoiceSession] = {}
        self.timeout_seconds = timeout_seconds

    def create_session(
        self,
        call_id: str,
        caller_number: str = "",
        trace_id: str = "",
        language: str = "hi",
    ) -> VoiceSession:
        session = VoiceSession(
            call_id=call_id,
            caller_number=caller_number,
            trace_id=trace_id,
            detected_language=language,
        )
        self._sessions[call_id] = session
        return session

    def get(self, call_id: str) -> Optional[VoiceSession]:
        session = self._sessions.get(call_id)
        if session and session.status == "active":
            # Timeout check
            if (time.time() - session.start_time) > self.timeout_seconds:
                session.drop()
                del self._sessions[call_id]
                return None
        return session

    def close(self, call_id: str) -> Optional[VoiceSession]:
        return self._sessions.pop(call_id, None)

    def list_active(self) -> list[str]:
        return [cid for cid, s in self._sessions.items() if s.status == "active"]

    def active_count(self) -> int:
        return sum(1 for s in self._sessions.values() if s.status == "active")
