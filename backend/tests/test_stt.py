
from typing import Any

import pytest
from app.core.container import Container
from app.stt.azure_provider import AzureProvider
from app.stt.fallback_provider import FallbackProvider
from app.stt.google_provider import GoogleProvider
from app.stt.provider_base import STTResult
from app.stt.provider_registry import ProviderRegistry
from app.stt.stt_manager import STTManager
from app.stt.whisper_provider import WhisperProvider


def test_stt_providers_instantiation() -> None:
    whisper = WhisperProvider()
    azure = AzureProvider()
    google = GoogleProvider()
    fallback = FallbackProvider()

    assert whisper.provider_name == "whisper"
    assert azure.provider_name == "azure"
    assert google.provider_name == "google"
    assert fallback.provider_name == "fallback"


def test_provider_registry() -> None:
    registry = ProviderRegistry()
    whisper = WhisperProvider()
    fallback = FallbackProvider()

    registry.register(whisper)
    registry.register(fallback)

    assert registry.get("whisper") is whisper
    assert registry.get("fallback") is fallback
    assert "whisper" in registry.list_providers()

    registry.set_active("fallback")
    assert registry.get_active() is fallback


@pytest.mark.asyncio
async def test_stt_manager_selection_and_transcribe() -> None:
    registry = ProviderRegistry()
    fallback = FallbackProvider()
    registry.register(fallback)
    registry.set_active("fallback")

    manager = STTManager(registry)
    # Test simple transcription
    res = await manager.transcribe(b"hello world", language="en")
    assert res.transcript == "hello world"
    assert res.provider == "fallback"
    assert res.language == "en"


@pytest.mark.asyncio
async def test_stt_manager_fallback_strategy() -> None:
    registry = ProviderRegistry()

    # Mock a failing provider (e.g. Whisper)
    failing_whisper = WhisperProvider(api_key="mock_key")
    # Stub transcribe to raise exception
    async def fail_transcribe(*args: Any, **kwargs: Any) -> STTResult:
        raise ValueError("Simulated network timeout")
    failing_whisper.transcribe = fail_transcribe

    # Working fallback provider
    working_fallback = FallbackProvider()

    registry.register(failing_whisper)
    registry.register(working_fallback)
    registry.set_active("whisper")

    # The manager has fallback_sequence = ["whisper", "google", "azure", "fallback"]
    manager = STTManager(registry)

    # Transcribe should fail on whisper but fallback to working_fallback and succeed
    res = await manager.transcribe(b"wheat disease check", language="en")
    assert res.transcript == "wheat disease check"
    assert res.provider == "fallback"  # Came from fallback provider
    assert res.confidence == 0.80


@pytest.mark.asyncio
async def test_stt_manager_language_detection() -> None:
    registry = ProviderRegistry()
    fallback = FallbackProvider()
    registry.register(fallback)
    registry.set_active("fallback")

    manager = STTManager(registry)

    # Test auto-detection heuristics
    res_en = await manager.transcribe("Is it going to rain in Ludhiana?".encode("utf-8"), language="auto")
    assert res_en.language == "en"

    res_hi = await manager.transcribe("नमस्ते मौसम कैसा है".encode("utf-8"), language="auto")
    assert res_hi.language == "hi"

    res_kn = await manager.transcribe("ನಮಸ್ಕಾರ ಬೆಳೆ".encode("utf-8"), language="auto")
    assert res_kn.language == "kn"

    res_te = await manager.transcribe("నమస్కారం వాతావరణం".encode("utf-8"), language="auto")
    assert res_te.language == "te"

    res_ta = await manager.transcribe("வணக்கம் பயிர்".encode("utf-8"), language="auto")
    assert res_ta.language == "ta"


@pytest.mark.asyncio
async def test_ivr_integration_stt_manager() -> None:
    container = Container()

    # Verify new stt_manager is mounted on container
    assert hasattr(container, "stt_manager")
    assert isinstance(container.stt_manager, STTManager)

    # Setup session
    session = container.call_session_manager.create_session("call-stt-ivr-test", language="en")

    # Execute handle_voice_recording
    from app.ivr.call_manager import CallManager
    call_mgr = CallManager(container)

    audio_data = b"What is the market price of rice?"
    res = await call_mgr.handle_voice_recording("call-stt-ivr-test", audio_data)
    assert res["success"] is True
    assert res["current_state"] == "CONFIRMATION"
    assert "What is the market price of rice?" in session.transcript[-2].text
