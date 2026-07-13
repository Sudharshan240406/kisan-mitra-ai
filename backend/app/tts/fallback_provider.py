import logging
import time
from typing import Any, Optional

from app.tts.provider_base import TTSResult, estimate_duration_ms

logger = logging.getLogger("kisan_mitra_ai.tts.fallback_provider")


class FallbackProvider:
    """Local fallback TTS provider that encodes input text as raw bytes."""
    provider_name = "fallback"

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult:
        start_time = time.perf_counter()
        audio = text.encode("utf-8")
        latency = (time.perf_counter() - start_time) * 1000

        return TTSResult(
            audio_bytes=audio,
            format="LINEAR16",
            sample_rate=8000,
            duration_ms=estimate_duration_ms(text, language),
            latency_ms=latency,
            provider=self.provider_name,
            language=language
        )

    def health(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "status": "active"
        }
