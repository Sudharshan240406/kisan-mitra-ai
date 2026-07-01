from __future__ import annotations

from typing import Any, Optional

from app.media.media import MediaType


class MultimodalTelemetry:
    """Helper that records multimodal metrics into the shared telemetry framework."""

    def __init__(self, telemetry: Any, event_bus: Optional[Any] = None) -> None:
        self.telemetry = telemetry
        self.event_bus = event_bus

    def record_processing(
        self,
        media_type: MediaType,
        trace_id: str,
        session_id: str,
        latency_ms: float,
        confidence: float,
        provider_id: str,
        reasoning_integrated: bool,
    ) -> None:
        type_name = media_type.value
        self.telemetry.record("multimodal_processing_latency_ms", latency_ms, trace_id, session_id, {"media_type": type_name, "provider": provider_id})
        self.telemetry.record("multimodal_confidence", confidence, trace_id, session_id, {"media_type": type_name})
        self.telemetry.record("multimodal_reasoning_integration", 1 if reasoning_integrated else 0, trace_id, session_id, {"media_type": type_name})

        if media_type == MediaType.VOICE:
            self.telemetry.record("voice_session_count", 1, trace_id, session_id, {"provider": provider_id})
            self.telemetry.record("speech_processing_latency_ms", latency_ms, trace_id, session_id, {"provider": provider_id})
            self.telemetry.record("speech_confidence", confidence, trace_id, session_id, {"provider": provider_id})
        elif media_type in {MediaType.IMAGE, MediaType.DRONE_IMAGE}:
            self.telemetry.record("vision_upload_count", 1, trace_id, session_id, {"provider": provider_id, "media_type": type_name})
            self.telemetry.record("vision_processing_latency_ms", latency_ms, trace_id, session_id, {"provider": provider_id, "media_type": type_name})
            self.telemetry.record("vision_confidence", confidence, trace_id, session_id, {"provider": provider_id, "media_type": type_name})
        elif media_type == MediaType.DOCUMENT:
            self.telemetry.record("ocr_request_count", 1, trace_id, session_id, {"provider": provider_id})
            self.telemetry.record("ocr_processing_latency_ms", latency_ms, trace_id, session_id, {"provider": provider_id})
            self.telemetry.record("ocr_confidence", confidence, trace_id, session_id, {"provider": provider_id})
