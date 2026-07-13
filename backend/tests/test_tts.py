from typing import Any

import pytest
from app.core.container import Container
from app.tts.azure_provider import AzureProvider
from app.tts.coqui_provider import CoquiProvider
from app.tts.elevenlabs_provider import ElevenLabsProvider
from app.tts.fallback_provider import FallbackProvider
from app.tts.google_provider import GoogleProvider
from app.tts.provider_base import TTSResult
from app.tts.provider_registry import ProviderRegistry
from app.tts.tts_manager import TTSManager


def test_tts_providers_instantiation() -> None:
    azure = AzureProvider()
    google = GoogleProvider()
    elevenlabs = ElevenLabsProvider()
    coqui = CoquiProvider()
    fallback = FallbackProvider()

    assert azure.provider_name == "azure"
    assert google.provider_name == "google"
    assert elevenlabs.provider_name == "elevenlabs"
    assert coqui.provider_name == "coqui"
    assert fallback.provider_name == "fallback"


def test_provider_registry() -> None:
    registry = ProviderRegistry()
    google = GoogleProvider()
    fallback = FallbackProvider()

    registry.register(google)
    registry.register(fallback)

    assert registry.get("google") is google
    assert registry.get("fallback") is fallback
    assert "google" in registry.list_providers()

    registry.set_active("fallback")
    assert registry.get_active() is fallback


@pytest.mark.asyncio
async def test_tts_manager_selection_and_synthesize() -> None:
    registry = ProviderRegistry()
    fallback = FallbackProvider()
    registry.register(fallback)
    registry.set_active("fallback")

    manager = TTSManager(registry)
    # Test simple synthesis
    res = await manager.synthesize(text="hello farmer", language="en")
    assert res.audio_bytes == b"hello farmer"
    assert res.provider == "fallback"
    assert res.language == "en"
    assert res.duration_ms > 0.0


@pytest.mark.asyncio
async def test_tts_manager_fallback_strategy() -> None:
    registry = ProviderRegistry()

    # Mock a failing provider
    failing_google = GoogleProvider(api_key="mock_key")
    async def fail_synthesize(*args: Any, **kwargs: Any) -> TTSResult:
        raise ValueError("Simulated network timeout")
    failing_google.synthesize = fail_synthesize

    # Working fallback provider
    working_fallback = FallbackProvider()

    registry.register(failing_google)
    registry.register(working_fallback)
    registry.set_active("google")

    manager = TTSManager(registry)

    # Synthesis should fail on google but fallback to working_fallback and succeed
    res = await manager.synthesize(text="crop protection report", language="en")
    assert res.audio_bytes == b"crop protection report"
    assert res.provider == "fallback"
    assert res.duration_ms > 0.0


@pytest.mark.asyncio
async def test_tts_manager_voice_profiles() -> None:
    registry = ProviderRegistry()
    fallback = FallbackProvider()
    registry.register(fallback)
    registry.set_active("fallback")

    manager = TTSManager(registry)

    # Test male profile
    res_male = await manager.synthesize("test", language="en", voice_profile="male")
    assert res_male.language == "en"

    # Test female profile
    res_female = await manager.synthesize("test", language="hi", voice_profile="female")
    assert res_female.language == "hi"

    # Test neural profile
    res_neural = await manager.synthesize("test", language="kn", voice_profile="neural")
    assert res_neural.language == "kn"


@pytest.mark.asyncio
async def test_ivr_integration_tts_manager() -> None:
    container = Container()

    # Verify new tts_manager is mounted on container
    assert hasattr(container, "tts_manager")
    assert isinstance(container.tts_manager, TTSManager)

    # Setup session
    _session = container.call_session_manager.create_session("call-tts-ivr-test", language="en")

    # Execute handle_voice_recording
    from app.ivr.call_manager import CallManager
    call_mgr = CallManager(container)

    audio_data = b"What is the weather like?"
    res = await call_mgr.handle_voice_recording("call-tts-ivr-test", audio_data)
    assert res["success"] is True
    assert res["current_state"] == "CONFIRMATION"
    # Verify response contains the tts audio prompt
    assert len(res["tts_prompt"]) > 0
