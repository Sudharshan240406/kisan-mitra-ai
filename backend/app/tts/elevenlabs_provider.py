import logging
import time
from typing import Any, Optional

import httpx
from app.tts.provider_base import TTSResult, estimate_duration_ms

logger = logging.getLogger("kisan_mitra_ai.tts.elevenlabs_provider")


class ElevenLabsProvider:
    """ElevenLabs Text-to-Speech API adapter."""
    provider_name = "elevenlabs"

    def __init__(self, api_key: str = "", default_voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> None:
        self._api_key = api_key
        self._default_voice_id = default_voice_id

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        streaming: bool = False,
    ) -> TTSResult:
        start_time = time.perf_counter()
        voice_id = voice_profile or self._default_voice_id

        if self._api_key:
            try:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "xi-api-key": self._api_key,
                    "Content-Type": "application/json",
                    "accept": "audio/mpeg"
                }
                payload = {
                    "text": text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.5,
                        "similarity_boost": 0.75
                    }
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        latency = (time.perf_counter() - start_time) * 1000
                        return TTSResult(
                            audio_bytes=response.content,
                            format="MP3",
                            sample_rate=8000,
                            duration_ms=estimate_duration_ms(text, language),
                            latency_ms=latency,
                            provider=self.provider_name,
                            language=language
                        )
            except Exception as e:
                logger.warning(f"ElevenLabs TTS call failed: {e}")

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
            "status": "active" if self._api_key else "stub",
            "api_key_configured": bool(self._api_key)
        }
