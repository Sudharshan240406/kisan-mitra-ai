import logging
import time
from typing import Any, Optional

import httpx
from app.stt.provider_base import BaseSTTProvider, STTResult

logger = logging.getLogger("kisan_mitra_ai.stt.azure_provider")


class AzureProvider:
    """Azure Cognitive Services Speech SDK adapter."""
    provider_name = "azure"

    def __init__(self, subscription_key: str = "", region: str = "eastasia") -> None:
        self._key = subscription_key
        self._region = region

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        sample_rate: int = 8000,
        encoding: str = "LINEAR16",
    ) -> STTResult:
        start_time = time.perf_counter()
        target_language = language if language and language != "auto" else "hi"

        if self._key:
            try:
                url = f"https://{self._region}.stt.speech.microsoft.com/speech/recognition/conversation/cognitiveservices/v1?language={target_language}"
                headers = {
                    "Ocp-Apim-Subscription-Key": self._key,
                    "Content-Type": "audio/wav"
                }
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.post(url, content=audio_bytes, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        text = data.get("DisplayText", "")
                        latency = (time.perf_counter() - start_time) * 1000
                        return STTResult(
                            transcript=text,
                            confidence=0.90,
                            language=target_language,
                            latency_ms=latency,
                            provider=self.provider_name
                        )
            except Exception as e:
                logger.warning(f"Azure Speech API call failed: {e}")

        # Fallback/stub behavior for local testing
        try:
            text = audio_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = "[audio content — Azure STT would transcribe here]"

        latency = (time.perf_counter() - start_time) * 1000
        return STTResult(
            transcript=text,
            confidence=0.90,
            language=target_language,
            latency_ms=latency,
            provider=self.provider_name
        )

    def health(self) -> dict[str, Any]:
        return {
            "provider": self.provider_name,
            "status": "active" if self._key else "stub",
            "region": self._region
        }
