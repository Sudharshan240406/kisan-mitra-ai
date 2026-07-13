import base64
import logging
import time
from typing import Any, Optional

import httpx
from app.tts.provider_base import TTSResult, estimate_duration_ms

logger = logging.getLogger("kisan_mitra_ai.tts.google_provider")


class GoogleProvider:
    """Google Cloud Text-to-Speech adapter."""
    provider_name = "google"

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
        start_time = time.perf_counter()

        if self._api_key:
            try:
                url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self._api_key}"
                lang_code = f"{language}-IN" if language != "en" else "en-US"

                payload = {
                    "input": {"text": text},
                    "voice": {
                        "languageCode": lang_code,
                        "name": voice_profile or (f"{lang_code}-Wavenet-A" if language != "en" else "en-US-Wavenet-F")
                    },
                    "audioConfig": {
                        "audioEncoding": "LINEAR16",
                        "speakingRate": speed,
                        "sampleRateHertz": 8000
                    }
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.post(url, json=payload)
                    if response.status_code == 200:
                        audio_content = base64.b64decode(response.json().get("audioContent", ""))
                        latency = (time.perf_counter() - start_time) * 1000
                        return TTSResult(
                            audio_bytes=audio_content,
                            format="LINEAR16",
                            sample_rate=8000,
                            duration_ms=estimate_duration_ms(text, language),
                            latency_ms=latency,
                            provider=self.provider_name,
                            language=language
                        )
            except Exception as e:
                logger.warning(f"Google TTS call failed: {e}")

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
