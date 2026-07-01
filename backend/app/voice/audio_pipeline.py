"""
Kisan Mitra AI — Audio Pipeline
==================================
Handles raw audio ingestion, format normalization, VAD (Voice Activity Detection),
chunking, and pre-processing for the STT layer.

For feature phone callers (₹500 phone / PSTN):
  - Input: 8kHz, LINEAR16, mono
  - Processing: silence trimming, amplitude normalization
  - Output: clean PCM bytes ready for STT provider
"""
from __future__ import annotations

import logging
import struct
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.voice.audio_pipeline")


# ---------------------------------------------------------------------------
# Audio Metadata
# ---------------------------------------------------------------------------

class AudioMetadata(BaseModel):
    """Metadata attached to processed audio chunks."""
    format: str = "LINEAR16"
    sample_rate: int = 8000
    channels: int = 1
    duration_ms: float = 0.0
    original_size_bytes: int = 0
    processed_size_bytes: int = 0
    vad_detected: bool = True          # voice activity detected
    silence_trimmed_ms: float = 0.0
    amplitude_normalized: bool = False


class ProcessedAudio(BaseModel):
    """Result of audio pipeline processing."""
    audio_bytes: bytes = b""
    metadata: AudioMetadata = Field(default_factory=AudioMetadata)
    success: bool = True
    error: str = ""

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# AudioPipeline
# ---------------------------------------------------------------------------

class AudioPipeline:
    """
    Audio pre-processing pipeline for voice calls.

    Responsibilities:
      1. Format validation: checks for supported audio formats.
      2. Silence detection: heuristic VAD based on amplitude.
      3. Silence trimming: removes leading/trailing silence.
      4. Amplitude normalization: scales audio to consistent level.
      5. Chunking: splits long audio for streaming STT.

    Design principle: conservative processing — prefer less alteration
    to avoid introducing artifacts that hurt STT accuracy.
    """

    SUPPORTED_FORMATS = {"LINEAR16", "WAV", "FLAC", "OGG_OPUS", "MP3"}
    MAX_AUDIO_BYTES = 5 * 1024 * 1024  # 5 MB limit

    def __init__(
        self,
        sample_rate: int = 8000,
        vad_silence_threshold: int = 100,    # amplitude RMS below = silence
        vad_min_speech_ms: int = 200,        # minimum speech to be valid
    ) -> None:
        self.sample_rate = sample_rate
        self.vad_silence_threshold = vad_silence_threshold
        self.vad_min_speech_ms = vad_min_speech_ms

    async def process(
        self,
        audio_bytes: bytes,
        fmt: str = "LINEAR16",
        sample_rate: int = 8000,
    ) -> ProcessedAudio:
        """
        Ingests raw audio bytes and returns clean, normalized audio
        ready for the STT provider.
        """
        original_size = len(audio_bytes)

        # Validation
        if not audio_bytes:
            return ProcessedAudio(success=False, error="Empty audio input.")
        if original_size > self.MAX_AUDIO_BYTES:
            return ProcessedAudio(success=False, error=f"Audio too large: {original_size} bytes.")
        if fmt.upper() not in self.SUPPORTED_FORMATS:
            return ProcessedAudio(success=False, error=f"Unsupported format: {fmt}.")

        # Duration estimate for LINEAR16 8kHz mono
        duration_ms = self._estimate_duration_ms(audio_bytes, sample_rate)

        # VAD — simple amplitude-based voice activity detection
        vad_detected, trimmed_bytes, silence_trimmed_ms = self._vad_and_trim(audio_bytes, sample_rate)

        # Amplitude normalization
        normalized, normalized_bytes = self._normalize_amplitude(trimmed_bytes)

        meta = AudioMetadata(
            format=fmt.upper(),
            sample_rate=sample_rate,
            channels=1,
            duration_ms=duration_ms,
            original_size_bytes=original_size,
            processed_size_bytes=len(normalized_bytes),
            vad_detected=vad_detected,
            silence_trimmed_ms=silence_trimmed_ms,
            amplitude_normalized=normalized,
        )
        logger.debug(
            f"[AudioPipeline] Processed {original_size}B → {len(normalized_bytes)}B, "
            f"VAD={vad_detected}, duration={duration_ms:.0f}ms"
        )
        return ProcessedAudio(audio_bytes=normalized_bytes, metadata=meta)

    def _estimate_duration_ms(self, audio_bytes: bytes, sample_rate: int) -> float:
        """For LINEAR16 mono: duration = bytes / (sample_rate * 2)."""
        try:
            return round(len(audio_bytes) / (sample_rate * 2) * 1000, 1)
        except ZeroDivisionError:
            return 0.0

    def _vad_and_trim(
        self, audio_bytes: bytes, sample_rate: int
    ) -> tuple[bool, bytes, float]:
        """
        Simple amplitude-based VAD: compute RMS energy of the audio.
        If RMS < threshold → no voice activity detected.
        Trims leading/trailing silence frames.
        """
        if len(audio_bytes) < 2:
            return False, audio_bytes, 0.0

        # Parse as 16-bit PCM samples
        try:
            num_samples = len(audio_bytes) // 2
            samples = struct.unpack(f"<{num_samples}h", audio_bytes[:num_samples * 2])
        except struct.error:
            return True, audio_bytes, 0.0  # Skip VAD if unparseable

        if not samples:
            return False, audio_bytes, 0.0

        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        vad_detected = rms >= self.vad_silence_threshold

        # Trim silence: 20ms frames
        frame_size = max(1, sample_rate * 20 // 1000)  # samples per 20ms
        frames = [samples[i:i + frame_size] for i in range(0, len(samples), frame_size)]
        active = [
            i for i, f in enumerate(frames)
            if (sum(s * s for s in f) / max(len(f), 1)) ** 0.5 >= self.vad_silence_threshold
        ]

        if not active:
            return False, audio_bytes, 0.0

        first, last = active[0], active[-1] + 1
        trimmed_samples = samples[first * frame_size: last * frame_size]
        trimmed_bytes = struct.pack(f"<{len(trimmed_samples)}h", *trimmed_samples)
        silence_trimmed_ms = round((len(samples) - len(trimmed_samples)) / sample_rate * 1000, 1)

        return vad_detected, trimmed_bytes, silence_trimmed_ms

    def _normalize_amplitude(self, audio_bytes: bytes) -> tuple[bool, bytes]:
        """
        Scales audio amplitude to target RMS level (0.1 of max).
        Returns (was_normalized, output_bytes).
        """
        if len(audio_bytes) < 2:
            return False, audio_bytes

        try:
            num_samples = len(audio_bytes) // 2
            samples = list(struct.unpack(f"<{num_samples}h", audio_bytes[:num_samples * 2]))
        except struct.error:
            return False, audio_bytes

        max_val = max(abs(s) for s in samples) if samples else 0
        if max_val == 0:
            return False, audio_bytes

        target = 16384  # ~50% of int16 max
        scale = target / max_val
        if 0.8 <= scale <= 1.2:
            return False, audio_bytes  # within acceptable range, skip

        normalized = [max(-32768, min(32767, int(s * scale))) for s in samples]
        out = struct.pack(f"<{len(normalized)}h", *normalized)
        return True, out

    def chunk(self, audio_bytes: bytes, chunk_ms: int = 3000, sample_rate: int = 8000) -> list[bytes]:
        """Splits audio into fixed-size chunks for streaming STT."""
        chunk_bytes = int(chunk_ms / 1000 * sample_rate * 2)  # bytes per chunk (16-bit)
        return [audio_bytes[i:i + chunk_bytes] for i in range(0, len(audio_bytes), chunk_bytes)]

    def health(self) -> dict[str, Any]:
        return {
            "component": "AudioPipeline",
            "sample_rate": self.sample_rate,
            "vad_threshold": self.vad_silence_threshold,
            "status": "healthy",
        }
