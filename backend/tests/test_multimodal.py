from __future__ import annotations

from app.core.telemetry import TelemetryFramework
from app.media.media import MediaInput, MediaMetadata, MediaResult, MediaType
from app.multimodal.core import MultimodalPlatform, VisionManager, VoiceManager
from app.multimodal.evidence import MultimodalEvidenceExtractor
from app.multimodal.telemetry import MultimodalTelemetry
from app.multimodal.validation import ImageValidationEngine
from app.voice.stt import STTProviderRegistry
from app.voice.tts import TTSProviderRegistry


class _DummyMediaRegistry:
    def list_providers(self) -> list[object]:
        return []


def test_image_validation_engine_rejects_blurry_dark_image() -> None:
    engine = ImageValidationEngine()
    media_input = MediaInput(
        media_type=MediaType.IMAGE,
        filename="leaf.png",
        content=b"image-bytes",
        metadata=MediaMetadata(
            file_size_bytes=128,
            format="png",
            additional_metadata={"blur_score": 0.2, "brightness_score": 0.2, "orientation_degrees": 0},
        ),
    )

    report = engine.validate(media_input)
    assert report.passed is False
    assert any("blurry" in err.lower() for err in report.errors)
    assert any("dark" in err.lower() for err in report.errors)


def test_multimodal_evidence_extractor_materializes_vision_payload() -> None:
    extractor = MultimodalEvidenceExtractor()
    result = MediaResult(
        media_id="MID-1",
        success=True,
        extracted_text="Leaf contains yellow spot patches indicative of rust.",
        confidence=0.91,
        evidence_payload=[{
            "id": "EV-1",
            "source": "image-mock",
            "agent": "Vision",
            "confidence": 0.91,
            "reasoning": "Leaf contains yellow spot patches indicative of rust.",
            "metadata": {"crop": "wheat"},
            "symptoms": ["yellow spots"],
            "pathogen": "yellow_rust",
        }],
    )
    context = MultimodalPlatform(
        voice_manager=VoiceManager(STTProviderRegistry(), TTSProviderRegistry()),
        vision_manager=VisionManager(_DummyMediaRegistry()),
    ).build_context(
        media_input=MediaInput(
            media_type=MediaType.IMAGE,
            filename="leaf.png",
            content=b"x",
            metadata=MediaMetadata(file_size_bytes=1, format="png"),
        ),
        conversation_id="conv-1",
        trace_id="trace-1",
    )

    evidences = extractor.extract(result, context)
    assert len(evidences) == 1
    assert evidences[0].agent == "Vision"
    assert evidences[0].metadata["crop"] == "wheat"


def test_multimodal_telemetry_exports_voice_vision_and_ocr_metrics() -> None:
    telemetry = TelemetryFramework()
    multimodal = MultimodalTelemetry(telemetry)

    multimodal.record_processing(MediaType.VOICE, "TR-1", "S-1", 12.0, 0.8, "voice-mock", True)
    multimodal.record_processing(MediaType.IMAGE, "TR-2", "S-2", 30.0, 0.7, "image-mock", True)
    multimodal.record_processing(MediaType.DOCUMENT, "TR-3", "S-3", 18.0, 0.9, "doc-mock", True)

    metrics = telemetry.export_metrics()
    assert metrics["voice_metrics"]["total_sessions"] == 1
    assert metrics["vision_metrics"]["total_uploads"] == 1
    assert metrics["ocr_metrics"]["total_requests"] == 1
    assert metrics["multimodal_metrics"]["reasoning_integration_rate"] == 1.0
