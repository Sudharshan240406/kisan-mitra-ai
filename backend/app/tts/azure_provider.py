import logging
import time
from typing import Any, Optional

import httpx
from app.tts.provider_base import TTSResult, estimate_duration_ms

logger = logging.getLogger("kisan_mitra_ai.tts.azure_provider")


class AzureProvider:
    """Azure Cognitive Services Text-to-Speech adapter."""
    provider_name = "azure"

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
        start_time = time.perf_counter()

        if self._key:
            try:
                url = f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/v1"
                headers = {
                    "Ocp-Apim-Subscription-Key": self._key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "riff-8khz-8bit-mono-mulaw",
                    "User-Agent": "KisanMitraAI"
                }

                # Format SSML
                gender = "Female" if voice_profile and "female" in voice_profile.lower() else "Male"
                voice_name = voice_profile or (
                    "en-US-JennyNeural" if language == "en" else "hi-IN-SwaraNeural"
                )
                rate_pct = f"{int((speed - 1.0) * 100):+d}%" if speed != 1.0 else "0%"

                ssml = f"""<speak version='1.0' xml:lang='{language}'>
                    <voice name='{voice_name}' gender='{gender}'>
                        <prosody rate='{rate_pct}'>{text}</prosody>
                    </voice>
                </speak>"""

                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.post(url, content=ssml, headers=headers)
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
                logger.warning(f"Azure TTS call failed: {e}")

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
            "status": "active" if self._key else "stub",
            "region": self._region
        }
