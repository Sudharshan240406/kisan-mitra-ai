import logging
from typing import Any, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.stt.provider_base")


class WordTimestamp(BaseModel):
    word: str
    start_ms: float
    end_ms: float
    confidence: float = 1.0


class STTResult(BaseModel):
    """Standardized output from any STT provider."""
    transcript: str = Field(..., description="Recognized speech text.")
    confidence: float = Field(..., description="Recognition confidence (0.0-1.0).")
    language: str = Field(default="hi", description="Detected or forced language code.")
    timestamps: List[WordTimestamp] = Field(default_factory=list)
    latency_ms: float = Field(default=0.0)
    provider: str = Field(default="unknown")
    alternatives: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class BaseSTTProvider(Protocol):
    """Protocol defining the standard interface for all STT adapters."""

    @property
    def provider_name(self) -> str:
        """Name identification of this provider instance."""
        ...

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        sample_rate: int = 8000,
        encoding: str = "LINEAR16",
    ) -> STTResult:
        """Transcribes audio bytes into text with language and confidence ratings."""
        ...

    def health(self) -> dict[str, Any]:
        """Provides status diagnostics information for checkups."""
        ...
