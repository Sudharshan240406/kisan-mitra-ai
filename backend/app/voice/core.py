"""
Kisan Mitra AI — Voice Platform Core
======================================
Bootstrap entry point for the Voice Intelligence & Telephony Platform.

Provides:
  - VoicePlatform: singleton registry + session lifecycle
  - VoiceMetrics: aggregate call-level performance counters
  - VoiceConfig: platform-wide configuration constants
  - VoiceSession registry (delegates to session.py)
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.voice.core")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

class VoiceConfig(BaseModel):
    """Platform-wide Voice Intelligence configuration."""
    default_language: str = "hi"
    supported_languages: list[str] = ["hi", "en", "kn", "te", "ta", "pa", "mr"]
    session_timeout_seconds: float = 300.0        # 5-minute call timeout
    max_transcript_length: int = 2000             # chars per turn
    max_conversation_turns: int = 20              # per session
    min_stt_confidence: float = 0.40             # escalate below this
    tts_speed_factor: float = 0.90               # slightly slower for farmers
    safety_confidence_threshold: float = 0.30    # escalate if overall conf < this
    max_retry_attempts: int = 3
    audio_sample_rate: int = 8000                # 8kHz for PSTN feature phones
    audio_encoding: str = "LINEAR16"
    vad_silence_ms: int = 1500                   # voice activity detection gap


# ---------------------------------------------------------------------------
# Voice Metrics
# ---------------------------------------------------------------------------

class VoiceMetrics(BaseModel):
    """Aggregate call-level performance counters."""
    total_calls: int = 0
    completed_calls: int = 0
    dropped_calls: int = 0
    escalated_calls: int = 0
    total_turns: int = 0

    # Latency
    avg_stt_latency_ms: float = 0.0
    avg_tts_latency_ms: float = 0.0
    avg_reasoning_latency_ms: float = 0.0
    avg_call_duration_seconds: float = 0.0

    # Quality
    avg_stt_confidence: float = 0.0
    avg_reasoning_confidence: float = 0.0
    escalation_rate: float = 0.0

    # Language distribution
    language_distribution: dict[str, int] = Field(default_factory=dict)

    # Internal accumulators
    _durations: list[float] = []
    _stt_confs: list[float] = []
    _rsn_confs: list[float] = []
    _stt_lats: list[float] = []
    _tts_lats: list[float] = []
    _rsn_lats: list[float] = []

    model_config = {"arbitrary_types_allowed": True}

    def record_call(
        self,
        duration_s: float,
        completed: bool,
        dropped: bool,
        escalated: bool,
        language: str,
        turns: int,
        stt_confidence: float,
        reasoning_confidence: float,
        stt_latency_ms: float,
        tts_latency_ms: float,
        reasoning_latency_ms: float,
    ) -> None:
        self.total_calls += 1
        if completed:
            self.completed_calls += 1
        if dropped:
            self.dropped_calls += 1
        if escalated:
            self.escalated_calls += 1
        self.total_turns += turns

        self._durations.append(duration_s)
        self._stt_confs.append(stt_confidence)
        self._rsn_confs.append(reasoning_confidence)
        self._stt_lats.append(stt_latency_ms)
        self._tts_lats.append(tts_latency_ms)
        self._rsn_lats.append(reasoning_latency_ms)

        self.language_distribution[language] = self.language_distribution.get(language, 0) + 1

        n = len(self._durations)
        self.avg_call_duration_seconds = round(sum(self._durations) / n, 2)
        self.avg_stt_confidence = round(sum(self._stt_confs) / n, 4)
        self.avg_reasoning_confidence = round(sum(self._rsn_confs) / n, 4)
        self.avg_stt_latency_ms = round(sum(self._stt_lats) / n, 2)
        self.avg_tts_latency_ms = round(sum(self._tts_lats) / n, 2)
        self.avg_reasoning_latency_ms = round(sum(self._rsn_lats) / n, 2)
        self.escalation_rate = round(self.escalated_calls / self.total_calls, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_calls": self.total_calls,
            "completed_calls": self.completed_calls,
            "dropped_calls": self.dropped_calls,
            "escalated_calls": self.escalated_calls,
            "total_turns": self.total_turns,
            "avg_stt_latency_ms": self.avg_stt_latency_ms,
            "avg_tts_latency_ms": self.avg_tts_latency_ms,
            "avg_reasoning_latency_ms": self.avg_reasoning_latency_ms,
            "avg_call_duration_seconds": self.avg_call_duration_seconds,
            "avg_stt_confidence": self.avg_stt_confidence,
            "avg_reasoning_confidence": self.avg_reasoning_confidence,
            "escalation_rate": self.escalation_rate,
            "language_distribution": self.language_distribution,
        }


# ---------------------------------------------------------------------------
# VoicePlatform
# ---------------------------------------------------------------------------

class VoicePlatform:
    """
    Bootstrap singleton for the Voice Intelligence & Telephony Platform.
    Holds the active session registry, configuration, and aggregate metrics.
    """

    def __init__(self, config: Optional[VoiceConfig] = None) -> None:
        self.config = config or VoiceConfig()
        self.metrics = VoiceMetrics()
        self._active_calls: dict[str, float] = {}   # call_id -> start_time
        self._component_registry: dict[str, Any] = {}
        logger.info("[VoicePlatform] Voice Intelligence Platform bootstrapped.")

    def register_component(self, name: str, component: Any) -> None:
        self._component_registry[name] = component
        logger.info(f"[VoicePlatform] Registered component: '{name}'")

    def get_component(self, name: str) -> Any:
        comp = self._component_registry.get(name)
        if comp is None:
            raise KeyError(f"[VoicePlatform] Component '{name}' not registered.")
        return comp

    def track_call_start(self, call_id: str) -> None:
        self._active_calls[call_id] = time.time()

    def track_call_end(self, call_id: str) -> float:
        """Returns duration in seconds and removes from active tracking."""
        start = self._active_calls.pop(call_id, time.time())
        return time.time() - start

    @property
    def active_call_count(self) -> int:
        return len(self._active_calls)

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "active_calls": self.active_call_count,
            "registered_components": list(self._component_registry.keys()),
            "metrics": self.metrics.to_dict(),
            "config": {
                "default_language": self.config.default_language,
                "supported_languages": self.config.supported_languages,
                "session_timeout_seconds": self.config.session_timeout_seconds,
            },
        }
