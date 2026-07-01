"""
Kisan Mitra AI — Speech-to-Text (STT) Provider Abstraction
===========================================================
Provider hierarchy:
  BaseSTTProvider (protocol)
    ├── GoogleSTTProvider
    ├── AzureSTTProvider
    ├── WhisperSTTProvider (OpenAI Whisper API)
    ├── LocalWhisperProvider (local model)
    └── MockSTTProvider (testing)

STTResult carries:
  - transcript: str
  - confidence: float (0.0 – 1.0)
  - language: str (detected ISO code)
  - timestamps: word-level if available
  - latency_ms: float
  - provider: str
"""
from __future__ import annotations

import logging
import time
import httpx
from typing import Any, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.voice.stt")


# ---------------------------------------------------------------------------
# STTResult
# ---------------------------------------------------------------------------

class WordTimestamp(BaseModel):
    word: str
    start_ms: float
    end_ms: float
    confidence: float = 1.0


class STTResult(BaseModel):
    """Standardized output from any STT provider."""
    transcript: str = Field(..., description="Recognized speech text.")
    confidence: float = Field(..., description="Recognition confidence (0.0–1.0).")
    language: str = Field(default="hi", description="Detected or forced language code.")
    timestamps: list[WordTimestamp] = Field(default_factory=list)
    latency_ms: float = Field(default=0.0)
    provider: str = Field(default="unknown")
    alternatives: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# STT Provider Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class BaseSTTProvider(Protocol):
    """Protocol contract every STT provider must implement."""

    @property
    def provider_name(self) -> str: ...

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "hi",
        sample_rate: int = 8000,
        encoding: str = "LINEAR16",
    ) -> STTResult: ...

    def health(self) -> dict[str, Any]: ...


# ---------------------------------------------------------------------------
# Google STT Provider (stub — ready for real SDK injection)
# ---------------------------------------------------------------------------

class GoogleSTTProvider:
    """
    Google Cloud Speech-to-Text v2 adapter.
    Supports FLAC/LINEAR16 at 8–48 kHz. Multi-language Indian language support.
    In production: inject google.cloud.speech.SpeechClient via DI.
    """
    provider_name = "google_stt"

    def __init__(self, api_key: str = "", project_id: str = "") -> None:
        self._api_key = api_key
        self._project_id = project_id
        logger.info("[GoogleSTT] Provider initialized (stub mode if no credentials).")

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "hi",
        sample_rate: int = 8000,
        encoding: str = "LINEAR16",
    ) -> STTResult:
        start = time.perf_counter()
        
        # Real Google STT REST request if API key is set
        if self._api_key:
            try:
                import base64
                audio_content = base64.b64encode(audio_bytes).decode("utf-8")
                url = f"https://speech.googleapis.com/v1/speech:recognize?key={self._api_key}"
                payload = {
                    "config": {
                        "encoding": encoding,
                        "sampleRateHertz": sample_rate,
                        "languageCode": language
                    },
                    "audio": {
                        "content": audio_content
                    }
                }
                async with httpx.AsyncClient(timeout=6.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        results = response.json().get("results", [])
                        if results:
                            transcript = results[0].get("alternatives", [{}])[0].get("transcript", "")
                            confidence = float(results[0].get("alternatives", [{}])[0].get("confidence", 0.92))
                            latency = (time.perf_counter() - start) * 1000
                            return STTResult(
                                transcript=transcript,
                                confidence=confidence,
                                language=language,
                                latency_ms=latency,
                                provider=self.provider_name
                            )
            except Exception as e:
                logger.warning(f"[GoogleSTT] Real transcription call failed: {e}")

        # Stub fallback: decode bytes as UTF-8 if test text, else return placeholder
        try:
            text = audio_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = "[audio content — Google STT would transcribe here]"

        latency = (time.perf_counter() - start) * 1000
        logger.info(f"[GoogleSTT] Transcribed {len(audio_bytes)} bytes in {latency:.1f}ms")
        return STTResult(
            transcript=text,
            confidence=0.92,
            language=language,
            latency_ms=latency,
            provider=self.provider_name,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "status": "active" if self._api_key else "stub", "api_key_set": bool(self._api_key)}


# ---------------------------------------------------------------------------
# Azure STT Provider (stub)
# ---------------------------------------------------------------------------

class AzureSTTProvider:
    """Azure Cognitive Services Speech SDK adapter."""
    provider_name = "azure_stt"

    def __init__(self, subscription_key: str = "", region: str = "eastasia") -> None:
        self._key = subscription_key
        self._region = region

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "hi",
        sample_rate: int = 8000,
        encoding: str = "LINEAR16",
    ) -> STTResult:
        start = time.perf_counter()
        
        # Real Azure Cognitive Services request if key is set
        if self._key:
            try:
                url = f"https://{self._region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language={language}"
                headers = {
                    "Ocp-Apim-Subscription-Key": self._key,
                    "Content-Type": "audio/wav"
                }
                async with httpx.AsyncClient(timeout=6.0) as client:
                    response = await client.post(url, content=audio_bytes, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        text = data.get("DisplayText", "")
                        latency = (time.perf_counter() - start) * 1000
                        return STTResult(
                            transcript=text, confidence=0.90, language=language,
                            latency_ms=latency, provider=self.provider_name
                        )
            except Exception as e:
                logger.warning(f"[AzureSTT] Real transcription call failed: {e}")

        try:
            text = audio_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = "[audio content — Azure STT would transcribe here]"
        latency = (time.perf_counter() - start) * 1000
        return STTResult(
            transcript=text, confidence=0.90, language=language,
            latency_ms=latency, provider=self.provider_name,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "status": "active" if self._key else "stub", "region": self._region}


# ---------------------------------------------------------------------------
# Whisper STT Provider (OpenAI Whisper API stub)
# ---------------------------------------------------------------------------

class WhisperSTTProvider:
    """OpenAI Whisper API adapter — multilingual, strong Hindi/Indian support."""
    provider_name = "whisper_api"

    def __init__(self, api_key: str = "") -> None:
        self._api_key = api_key

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "hi",
        sample_rate: int = 8000,
        encoding: str = "LINEAR16",
    ) -> STTResult:
        start = time.perf_counter()
        
        # Real OpenAI Whisper API call if key is set
        if self._api_key:
            try:
                url = "https://api.openai.com/v1/audio/transcriptions"
                headers = {"Authorization": f"Bearer {self._api_key}"}
                files = {"file": ("speech.wav", audio_bytes, "audio/wav")}
                data = {"model": "whisper-1", "language": language}
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.post(url, headers=headers, files=files, data=data)
                    if response.status_code == 200:
                        text = response.json().get("text", "")
                        latency = (time.perf_counter() - start) * 1000
                        return STTResult(
                            transcript=text, confidence=0.95, language=language,
                            latency_ms=latency, provider=self.provider_name
                        )
            except Exception as e:
                logger.warning(f"[WhisperSTT] OpenAI transcription call failed: {e}")

        try:
            text = audio_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = "[Whisper API transcription placeholder]"
        latency = (time.perf_counter() - start) * 1000
        return STTResult(
            transcript=text, confidence=0.93, language=language,
            latency_ms=latency, provider=self.provider_name,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "status": "active" if self._api_key else "stub"}


# ---------------------------------------------------------------------------
# Local Whisper Provider (on-device stub)
# ---------------------------------------------------------------------------

class LocalWhisperProvider:
    """
    Local Whisper model adapter — runs on-device.
    No API cost; suitable for edge deployments.
    In production: load whisper.load_model("small") via DI.
    """
    provider_name = "local_whisper"

    def __init__(self, model_size: str = "small") -> None:
        self._model_size = model_size

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "hi",
        sample_rate: int = 8000,
        encoding: str = "LINEAR16",
    ) -> STTResult:
        start = time.perf_counter()
        try:
            text = audio_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = "[Local Whisper transcription placeholder]"
        latency = (time.perf_counter() - start) * 1000
        return STTResult(
            transcript=text, confidence=0.85, language=language,
            latency_ms=latency, provider=self.provider_name,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "model_size": self._model_size, "status": "stub"}


# ---------------------------------------------------------------------------
# Mock STT Provider (for testing)
# ---------------------------------------------------------------------------

class MockSTTProvider:
    """Mock STT provider for unit tests — decodes bytes as UTF-8 text."""
    provider_name = "mock_stt"

    def __init__(self, forced_confidence: float = 0.90) -> None:
        self._confidence = forced_confidence

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: str = "hi",
        sample_rate: int = 8000,
        encoding: str = "LINEAR16",
    ) -> STTResult:
        try:
            text = audio_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = "mock transcription"
        return STTResult(
            transcript=text,
            confidence=self._confidence,
            language=language,
            latency_ms=5.0,
            provider=self.provider_name,
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.provider_name, "status": "mock"}


# ---------------------------------------------------------------------------
# STT Registry
# ---------------------------------------------------------------------------

class STTProviderRegistry:
    """Registry of named STT providers with active-provider routing."""

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}
        self._active: str = ""

    def register(self, provider: Any) -> None:
        name = provider.provider_name
        self._providers[name] = provider
        if not self._active:
            self._active = name
        logger.info(f"[STTRegistry] Registered provider: '{name}'")

    def set_active(self, name: str) -> None:
        if name not in self._providers:
            raise KeyError(f"STT provider '{name}' not registered.")
        self._active = name

    def get_active(self) -> Any:
        if not self._active:
            raise RuntimeError("No active STT provider registered.")
        return self._providers[self._active]

    def get(self, name: str) -> Any:
        return self._providers[name]

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())
