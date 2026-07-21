import logging
import time
from typing import Any, Optional

from app.stt.provider_base import STTResult

logger = logging.getLogger("kisan_mitra_ai.stt.fallback_provider")


class FallbackProvider:
    """Local stub fallback provider that decodes inputs or returns default placeholders."""
    provider_name = "fallback"

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        sample_rate: int = 8000,
        encoding: str = "LINEAR16",
    ) -> STTResult:
        start_time = time.perf_counter()
        target_language = language if language and language != "auto" else "hi"

        try:
            # Decode if it's plaintext for test harness mock text bypasses
            text = audio_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = "fallback transcript"

        latency = (time.perf_counter() - start_time) * 1000
        return STTResult(
            transcript=text,
            confidence=0.80,
            language=target_language,
            latency_ms=latency,
            provider=self.provider_name
        )

    def health(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "status": "active"
        }
