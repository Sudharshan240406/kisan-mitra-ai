import logging
import time
from typing import Any, Dict, Optional

from app.tts.provider_base import TTSResult, estimate_duration_ms
from app.tts.provider_registry import ProviderRegistry

logger = logging.getLogger("kisan_mitra_ai.tts.tts_manager")

# Configurable Voice Profiles Mapping by Language
VOICE_PROFILES: Dict[str, Dict[str, str]] = {
    "en": {
        "male": "en-US-Wavenet-B",
        "female": "en-US-JennyNeural",
        "natural": "en-US-Neural2-F",
        "neural": "en-US-JennyNeural"
    },
    "hi": {
        "male": "hi-IN-Neural2-B",
        "female": "hi-IN-SwaraNeural",
        "natural": "hi-IN-Wavenet-A",
        "neural": "hi-IN-SwaraNeural"
    },
    "kn": {
        "male": "kn-IN-Standard-B",
        "female": "kn-IN-Standard-A",
        "natural": "kn-IN-Standard-A",
        "neural": "kn-IN-Standard-A"
    },
    "te": {
        "male": "te-IN-Standard-B",
        "female": "te-IN-Standard-A",
        "natural": "te-IN-Standard-A",
        "neural": "te-IN-Standard-A"
    },
    "ta": {
        "male": "ta-IN-Standard-B",
        "female": "ta-IN-Standard-A",
        "natural": "ta-IN-Standard-A",
        "neural": "ta-IN-Standard-A"
    }
}


class TTSManager:
    """Orchestrates Text-to-Speech pipelines, failovers, and voice configurations."""

    def __init__(self, registry: ProviderRegistry, container: Any = None) -> None:
        self.registry = registry
        self.container = container
        # Default fallback sequence if the primary provider fails
        self.fallback_sequence = ["google", "azure", "elevenlabs", "coqui", "fallback"]

    async def synthesize(
        self,
        text: str,
        language: str = "hi",
        voice_profile: Optional[str] = None,
        speed: float = 0.90,
        provider: Optional[str] = None,
        streaming: bool = False,
    ) -> TTSResult:
        start_time = time.perf_counter()

        # 1. Resolve voice profile name
        resolved_voice_name = voice_profile
        profile_key = (voice_profile or "female").lower()
        if language in VOICE_PROFILES and profile_key in VOICE_PROFILES[language]:
            resolved_voice_name = VOICE_PROFILES[language][profile_key]

        # 2. Determine active provider
        selected_provider_name = provider or ""
        if not selected_provider_name:
            active_p = self.registry.get_active()
            selected_provider_name = active_p.provider_name if active_p else "fallback"

        # 3. Execution with Fallback Strategy
        retry_count = 0
        failure_count = 0
        final_result = None

        # Build queue
        execution_queue = [selected_provider_name]
        for p_name in self.fallback_sequence:
            if p_name not in execution_queue:
                execution_queue.append(p_name)

        for current_provider_name in execution_queue:
            provider_inst = self.registry.get(current_provider_name)
            if not provider_inst:
                continue

            try:
                logger.info(f"[TTSManager] Synthesizing via provider '{current_provider_name}'...")
                res = await provider_inst.synthesize(
                    text=text,
                    language=language,
                    voice_profile=resolved_voice_name,
                    speed=speed,
                    streaming=streaming
                )

                # Check for validity: non-empty audio
                if res and res.audio_bytes:
                    final_result = res
                    break
                else:
                    raise ValueError("Empty audio result returned.")

            except Exception as e:
                logger.warning(
                    f"[TTSManager] Provider '{current_provider_name}' synthesis failed: {e}. "
                    f"Switching to fallback."
                )
                failure_count += 1
                retry_count += 1

        # Fallback safeguard
        if not final_result:
            logger.error("[TTSManager] All providers failed. Executing fallback provider safeguard.")
            fb_inst = self.registry.get("fallback")
            if fb_inst:
                final_result = await fb_inst.synthesize(text, language=language, voice_profile=voice_profile, speed=speed)
            else:
                final_result = TTSResult(
                    audio_bytes=text.encode("utf-8"),
                    format="LINEAR16",
                    sample_rate=8000,
                    duration_ms=estimate_duration_ms(text, language),
                    latency_ms=0.0,
                    provider="unknown",
                    language=language
                )

        latency_ms = (time.perf_counter() - start_time) * 1000
        final_result.latency_ms = latency_ms

        # 4. Telemetry Observability Logging
        self._record_telemetry(
            provider=final_result.provider,
            latency_ms=latency_ms,
            audio_duration_ms=final_result.duration_ms,
            retries=retry_count,
            failures=failure_count
        )

        return final_result

    def _record_telemetry(
        self,
        provider: str,
        latency_ms: float,
        audio_duration_ms: float,
        retries: int,
        failures: int
    ) -> None:
        """Records diagnostic metrics to the container telemetry systems."""
        logger.info(
            f"[TTSTelemetry] provider={provider} latency={latency_ms:.1f}ms "
            f"duration={audio_duration_ms:.1f}ms retries={retries} failures={failures}"
        )
        if self.container and hasattr(self.container, "telemetry") and self.container.telemetry:
            try:
                trace_id = "tts_trace"
                session_id = "tts_session"
                self.container.telemetry.record("tts_latency_ms", latency_ms, trace_id, session_id)
                self.container.telemetry.record("tts_duration_ms", audio_duration_ms, trace_id, session_id)
                self.container.telemetry.record("tts_retries", float(retries), trace_id, session_id)
                self.container.telemetry.record("tts_failures", float(failures), trace_id, session_id)
            except Exception as e:
                logger.warning(f"Failed to publish TTS telemetry: {e}")
