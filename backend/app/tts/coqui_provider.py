import logging
import time
from typing import Any, Optional

import httpx
from app.tts.provider_base import TTSResult, estimate_duration_ms

logger = logging.getLogger("kisan_mitra_ai.tts.coqui_provider")


class CoquiProvider:
    """Coqui TTS service adapter (ideal for offline or self-hosted regional voices)."""
    provider_name = "coqui"

    def __init__(self, api_url: str = "") -> None:
        self._api_url = api_url

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult:
        start_time = time.perf_counter()

        if self._api_url:
            try:
                headers = {"Content-Type": "application/json"}
                payload = {
                    "text": text,
                    "language": language,
                    "speaker_id": voice_profile or "default"
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.post(f"{self._api_url}/api/tts", json=payload, headers=headers)
                    if response.status_code == 200:
                        latency = (time.perf_counter() - start_time) * 1000
                        return TTSResult(
                            audio_bytes=response.content,
                            format="LINEAR16",
                            sample_rate=8000,
                            duration_ms=estimate_duration_ms(text, language),
                            latency_ms=latency,
                            provider=self.provider_name,
                            language=language
                        )
            except Exception as e:
                logger.warning(f"Coqui TTS call failed: {e}")

        # Stub fallback: encode text as bytes
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
            "status": "active" if self._api_url else "stub",
            "api_url": self._api_url
        }
