"""
Kisan Mitra AI — Text-to-Speech (TTS) Provider Abstraction
===========================================================
Provider hierarchy:
  BaseTTSProvider (protocol)
    ├── GoogleTTSProvider
    ├── AzureTTSProvider
    ├── CoquiTTSProvider (open-source, Indian languages)
    ├── PiperTTSProvider (offline edge TTS)
    └── MockTTSProvider (testing)

TTSResult carries:
  - audio_bytes: bytes (PCM/MP3 depending on provider)
  - format: str ('LINEAR16', 'MP3', 'OGG_OPUS')
  - sample_rate: int
  - duration_ms: float (estimated speaking duration)
  - latency_ms: float (synthesis latency)
  - provider: str
  - language: str
  - interrupted: bool (True if farmer spoke over)
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.voice.tts")


# ---------------------------------------------------------------------------
# TTSResult
# ---------------------------------------------------------------------------

class TTSResult(BaseModel):
    """Standardized output from any TTS provider."""
    audio_bytes: bytes = Field(default=b"", description="Synthesized audio bytes.")
    format: str = Field(default="LINEAR16", description="Audio encoding format.")
    sample_rate: int = Field(default=8000, description="Audio sample rate in Hz.")
    duration_ms: float = Field(default=0.0, description="Estimated speaking duration.")
    latency_ms: float = Field(default=0.0, description="Synthesis latency in ms.")
    provider: str = Field(default="unknown")
    language: str = Field(default="hi")
    interrupted: bool = Field(default=False, description="True if farmer interrupted playback.")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# TTS Provider Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class BaseTTSProvider(Protocol):
    """Protocol contract every TTS provider must implement."""

    @property
    def provider_name(self) -> str: ...

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult: ...

    def health(self) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Helper: estimate speaking duration
# ---------------------------------------------------------------------------

def _estimate_duration_ms(text: str, language: str) -> float:
    """Rough estimate: Indian languages ~100 words/min, English ~130 words/min."""
    wpm = 100 if language != "en" else 130
    words = max(len(text.split()), 1)
    return round((words / wpm) * 60 * 1000, 1)


# ---------------------------------------------------------------------------
# Google TTS Provider (stub)
# ---------------------------------------------------------------------------

class GoogleTTSProvider:
    """
    Google Cloud Text-to-Speech adapter.
    Supports WaveNet voices for hi-IN, kn-IN, te-IN, ta-IN, pa-IN.
    In production: inject google.cloud.texttospeech.TextToSpeechClient via DI.
    """
    provider_name = "google_tts"

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult:
        start = time.perf_counter()
        # Stub: encode text as bytes (real impl would call Google TTS API)
        audio = text.encode("utf-8")
        latency = (time.perf_counter() - start) * 1000
        return TTSResult(
            audio_bytes=audio,
            format="LINEAR16",
            sample_rate=8000,
            duration_ms=_estimate_duration_ms(text, language),
            latency_ms=latency,
            provider=self.provider_name,
            language=language,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "status": "stub"}


# ---------------------------------------------------------------------------
# Azure TTS Provider (stub)
# ---------------------------------------------------------------------------

class AzureTTSProvider:
    """Azure Cognitive Services TTS adapter — Neural voices for Indian languages."""
    provider_name = "azure_tts"

    def __init__(self, subscription_key: str = "", region: str = "eastasia") -> None:
        self._key = subscription_key
        self._region = region

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult:
        start = time.perf_counter()
        audio = text.encode("utf-8")
        latency = (time.perf_counter() - start) * 1000
        return TTSResult(
            audio_bytes=audio, format="MP3", sample_rate=16000,
            duration_ms=_estimate_duration_ms(text, language),
            latency_ms=latency, provider=self.provider_name, language=language,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "status": "stub", "region": self._region}


# ---------------------------------------------------------------------------
# Coqui TTS Provider (open-source, Indian languages, stub)
# ---------------------------------------------------------------------------

class CoquiTTSProvider:
    """
    Coqui TTS adapter — open-source, supports Indian language models.
    Ideal for cost-free on-premise deployments.
    In production: inject TTS model via DI.
    """
    provider_name = "coqui_tts"

    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/your_tts") -> None:
        self._model_name = model_name

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult:
        audio = text.encode("utf-8")
        return TTSResult(
            audio_bytes=audio, format="WAV", sample_rate=22050,
            duration_ms=_estimate_duration_ms(text, language),
            latency_ms=15.0, provider=self.provider_name, language=language,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "model": self._model_name, "status": "stub"}


# ---------------------------------------------------------------------------
# Piper TTS Provider (offline edge, stub)
# ---------------------------------------------------------------------------

class PiperTTSProvider:
    """
    Piper TTS — ultra-fast offline neural TTS, ideal for edge deployments.
    Works on resource-constrained hardware (Raspberry Pi, edge nodes).
    In production: spawn piper subprocess or load model.
    """
    provider_name = "piper_tts"

    def __init__(self, model_path: str = "/models/piper/hi-IN-male.onnx") -> None:
        self._model_path = model_path

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult:
        audio = text.encode("utf-8")
        return TTSResult(
            audio_bytes=audio, format="WAV", sample_rate=16000,
            duration_ms=_estimate_duration_ms(text, language),
            latency_ms=8.0, provider=self.provider_name, language=language,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "model_path": self._model_path, "status": "stub"}


# ---------------------------------------------------------------------------
# Mock TTS Provider (testing)
# ---------------------------------------------------------------------------

class MockTTSProvider:
    """Mock TTS provider for unit tests — encodes text as UTF-8 bytes."""
    provider_name = "mock_tts"

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult:
        return TTSResult(
            audio_bytes=text.encode("utf-8"),
            format="LINEAR16",
            sample_rate=8000,
            duration_ms=_estimate_duration_ms(text, language),
            latency_ms=2.0,
            provider=self.provider_name,
            language=language,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "status": "mock"}


# ---------------------------------------------------------------------------
# TTS Registry
# ---------------------------------------------------------------------------

class TTSProviderRegistry:
    """Registry of named TTS providers with active-provider routing."""

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}
        self._active: str = ""

    def register(self, provider: Any) -> None:
        name = provider.provider_name
        self._providers[name] = provider
        if not self._active:
            self._active = name
        logger.info(f"[TTSRegistry] Registered provider: '{name}'")

    def set_active(self, name: str) -> None:
        if name not in self._providers:
            raise KeyError(f"TTS provider '{name}' not registered.")
        self._active = name

    def get_active(self) -> Any:
        if not self._active:
            raise RuntimeError("No active TTS provider registered.")
        return self._providers[self._active]

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())
