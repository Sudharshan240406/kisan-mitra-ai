import logging
from typing import Any, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.tts.provider_base")


class TTSResult(BaseModel):
    """Standardized output from any TTS provider."""
    audio_bytes: bytes = Field(default=b"", description="Synthesized audio bytes.")
    format: str = Field(default="LINEAR16", description="Audio encoding format.")
    sample_rate: int = Field(default=8000, description="Audio sample rate in Hz.")
    duration_ms: float = Field(default=0.0, description="Estimated speaking duration in ms.")
    latency_ms: float = Field(default=0.0, description="Synthesis latency in ms.")
    provider: str = Field(default="unknown")
    language: str = Field(default="hi")
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}


@runtime_checkable
class BaseTTSProvider(Protocol):
    """Protocol defining the standard interface for all TTS adapters."""

    @property
    def provider_name(self) -> str:
        """Name identification of this provider instance."""
        ...

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult:
        """Synthesizes text into audio streams using language settings."""
        ...

    def health(self) -> dict[str, Any]:
        """Provides status diagnostics information for checkups."""
        ...


def estimate_duration_ms(text: str, language: str) -> float:
    """Rough estimate: Indian languages ~100 words/min, English ~130 words/min."""
    wpm = 100 if language != "en" else 130
    words = max(len(text.split()), 1)
    return round((words / wpm) * 60 * 1000, 1)
