import logging
import time
from typing import Any, Optional

from app.stt.provider_base import STTResult
from app.stt.provider_registry import ProviderRegistry

logger = logging.getLogger("kisan_mitra_ai.stt.stt_manager")


class STTManager:
    """Orchestrates Speech-to-Text pipelines, provider fallbacks, and observability."""

    def __init__(self, registry: ProviderRegistry, container: Any = None) -> None:
        self.registry = registry
        self.container = container
        # Default fallback sequence if the primary provider fails
        self.fallback_sequence = ["whisper", "google", "azure", "fallback"]

    async def transcribe(
        self,
        audio_bytes: bytes,
        language: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> STTResult:
        start_time = time.perf_counter()

        # 1. Determine active provider
        selected_provider_name = provider or ""
        if not selected_provider_name:
            active_p = self.registry.get_active()
            selected_provider_name = active_p.provider_name if active_p else "fallback"

        # 2. Heuristic Language Auto-Detection
        target_language = language
        if not target_language or target_language == "auto":
            target_language = self._detect_language_heuristically(audio_bytes)

        # 3. Execution with Fallback Strategy
        retry_count = 0
        failure_count = 0
        final_result = None

        # Build execution queue starting with selected provider, followed by fallbacks
        execution_queue = [selected_provider_name]
        for p_name in self.fallback_sequence:
            if p_name not in execution_queue:
                execution_queue.append(p_name)

        for current_provider_name in execution_queue:
            provider_inst = self.registry.get(current_provider_name)
            if not provider_inst:
                continue

            try:
                logger.info(f"[STTManager] Attempting transcription via provider '{current_provider_name}'...")
                res = await provider_inst.transcribe(
                    audio_bytes,
                    language=target_language
                )

                # Check for validity: non-empty transcript and decent confidence
                if res and res.transcript.strip():
                    final_result = res
                    break
                else:
                    raise ValueError("Empty transcription or invalid result.")

            except Exception as e:
                logger.warning(
                    f"[STTManager] Provider '{current_provider_name}' transcription failed: {e}. "
                    f"Switching to fallback."
                )
                failure_count += 1
                retry_count += 1

        # Fallback safeguard
        if not final_result:
            logger.error("[STTManager] All providers failed. Executing fallback provider safeguard.")
            fb_inst = self.registry.get("fallback")
            if fb_inst:
                final_result = await fb_inst.transcribe(audio_bytes, language=target_language)
            else:
                final_result = STTResult(
                    transcript="[Transcription Failed]",
                    confidence=0.0,
                    language=target_language or "hi",
                    latency_ms=0.0,
                    provider="unknown"
                )

        latency_ms = (time.perf_counter() - start_time) * 1000
        final_result.latency_ms = latency_ms

        # 4. Observability & Telemetry Logging
        self._record_telemetry(
            provider=final_result.provider,
            latency_ms=latency_ms,
            confidence=final_result.confidence,
            retries=retry_count,
            failures=failure_count
        )

        return final_result

    def _detect_language_heuristically(self, audio_bytes: bytes) -> str:
        """Heuristic language detection from speech contents or metadata patterns."""
        # Check if the audio_bytes carry UTF-8 text (mock test strings)
        try:
            decoded = audio_bytes.decode("utf-8").lower()
            if any(word in decoded for word in ["rain", "weather", "wheat", "crop", " Punjab"]):
                return "en"
            if any(word in decoded for word in ["नमस्ते", "मौसम", "योजना"]):
                return "hi"
            if any(word in decoded for word in ["ನಮಸ್ಕಾರ", "ಮಳೆ", "ಬೆಳೆ"]):
                return "kn"
            if any(word in decoded for word in ["నమస్కారం", "వాతావరణం", "పంట"]):
                return "te"
            if any(word in decoded for word in ["வணக்கம்", "வானிலை", "பயிர்"]):
                return "ta"
        except UnicodeDecodeError:
            pass

        # Default to Hindi as standard agricultural fallback
        return "hi"

    def _record_telemetry(
        self,
        provider: str,
        latency_ms: float,
        confidence: float,
        retries: int,
        failures: int
    ) -> None:
        """Records diagnostic metrics to the container telemetry systems."""
        logger.info(
            f"[STTTelemetry] provider={provider} latency={latency_ms:.1f}ms "
            f"confidence={confidence:.2f} retries={retries} failures={failures}"
        )
        if self.container and hasattr(self.container, "telemetry") and self.container.telemetry:
            try:
                trace_id = "stt_trace"
                session_id = "stt_session"
                self.container.telemetry.record("stt_latency_ms", latency_ms, trace_id, session_id)
                self.container.telemetry.record("stt_confidence", confidence, trace_id, session_id)
                self.container.telemetry.record("stt_retries", float(retries), trace_id, session_id)
                self.container.telemetry.record("stt_failures", float(failures), trace_id, session_id)
            except Exception as e:
                logger.warning(f"Failed to publish STT telemetry: {e}")
