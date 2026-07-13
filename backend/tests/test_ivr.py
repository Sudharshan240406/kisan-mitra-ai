import time
import pytest
from typing import Any
from unittest.mock import MagicMock, AsyncMock

from app.core.container import Container
from app.ivr.call_session import CallSession, CallSessionState
from app.ivr.ivr_flow import IVRFlow, IVRState, IVRStateMachine
from app.ivr.language_selector import LanguageSelector
from app.ivr.dtmf_handler import DTMFHandler
from app.ivr.transcript_manager import TranscriptManager
from app.ivr.summary_generator import SummaryGenerator
from app.ivr.call_manager import CallManager
from app.personalization.models import FarmerProfile


def test_ivr_flow_prompts() -> None:
    flow = IVRFlow()
    # Test multilingual greeting prompt
    assert "नमस्ते" in flow.get_prompt("GREETING", "hi")
    assert "welcome" in flow.get_prompt("GREETING", "en").lower()
    assert "ನಮಸ್ಕಾರ" in flow.get_prompt("GREETING", "kn")
    assert "నమస్కారం" in flow.get_prompt("GREETING", "te")
    assert "வணக்கம்" in flow.get_prompt("GREETING", "ta")
    assert "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ" in flow.get_prompt("GREETING", "pa")

    # Test fallback
    assert "welcome" in flow.get_prompt("GREETING", "invalid-lang").lower()


@pytest.mark.asyncio
async def test_language_selector_digital_twin() -> None:
    # Mock Twin Manager
    twin_manager = MagicMock()
    mock_twin = MagicMock()
    mock_profile = FarmerProfile(farmer_id="Ramesh-001", name="Ramesh")
    mock_twin.profile = mock_profile
    twin_manager.get_twin.return_value = mock_twin

    selector = LanguageSelector(None)
    # mock container wrapper
    selector.container = MagicMock()
    selector.container.twin_manager = twin_manager

    # Create dummy session
    session = CallSession(call_id="call-123", farmer_id="Ramesh-001")
    
    # Select Kannada
    selector.select_language(session, "kn")
    assert session.language == "kn"
    assert mock_profile.preferred_language == "kn"
    twin_manager.update_twin.assert_called_once_with(mock_twin)


@pytest.mark.asyncio
async def test_dtmf_handler_transitions() -> None:
    flow = IVRFlow()
    selector = MagicMock()
    handler = DTMFHandler(flow, selector)

    session = CallSession(call_id="call-456", language="en")
    session.current_ivr_state = "LANGUAGE_SELECTION"

    # Press 3 for Kannada
    next_state, prompt = await handler.handle_dtmf(session, "3")
    assert session.current_ivr_state == "CALLER_IDENTIFICATION"
    selector.select_language.assert_called_once_with(session, "kn")
    assert "Press 1" in prompt  # English prompt fallback for next state


@pytest.mark.asyncio
async def test_transcript_manager_logging() -> None:
    session = CallSession(call_id="call-789")
    tm = TranscriptManager()
    
    tm.add_entry(session, "farmer", "Hello Mitra", confidence=0.98, timing_ms=25.0)
    assert len(session.transcript) == 1
    assert session.transcript[0].sender == "farmer"
    assert session.transcript[0].text == "Hello Mitra"
    assert session.transcript[0].confidence == 0.98
    assert session.transcript[0].timing_ms == 25.0


@pytest.mark.asyncio
async def test_summary_generator_persists() -> None:
    container = Container()
    sg = SummaryGenerator(container)

    session = CallSession(call_id="call-summ", farmer_id="Ramesh-001")
    tm = TranscriptManager()
    tm.add_entry(session, "farmer", "Tell me the weather and government scheme details.")
    tm.add_entry(session, "system", "It will rain tomorrow. PM Kisan Samman Nidhi is active.")

    summary = await sg.generate_and_store_summary(session)
    assert summary.weather_advice != ""
    assert "Government Scheme" in summary.recommended_schemes or len(summary.recommended_schemes) >= 0
    assert session.summary == summary

    # Retrieve from Memory Engine
    memory = container.personalization_platform.memories.get("Ramesh-001")
    assert memory is not None
    assert len(memory.historical_outcomes) == 1
    assert memory.historical_outcomes[0]["call_id"] == "call-summ"


@pytest.mark.asyncio
async def test_call_manager_lifecycle_e2e() -> None:
    container = Container()
    
    # Mock twin manager and websocket manager in container
    container.twin_manager = MagicMock()
    mock_twin = MagicMock()
    mock_twin.profile = FarmerProfile(farmer_id="Ramesh-001", name="Ramesh")
    container.twin_manager.get_twin.return_value = mock_twin

    manager = CallManager(container)

    # 1. Incoming Call
    res = await manager.handle_incoming_call(caller="+9199999", callee="+9188888", call_id="call-ivr-test")
    assert res["success"] is True
    assert res["current_state"] == "LANGUAGE_SELECTION"
    
    session = container.call_session_manager.get_session("call-ivr-test")
    assert session is not None
    assert session.language == "hi"

    # 2. Select Language to English (Press 2)
    res_lang = await manager.handle_dtmf_input("call-ivr-test", "2")
    assert res_lang["success"] is True
    assert session.language == "en"
    assert res_lang["current_state"] == "CALLER_IDENTIFICATION"

    # 3. Caller type guest (Press 3)
    res_type = await manager.handle_dtmf_input("call-ivr-test", "3")
    assert res_type["success"] is True
    assert res_type["current_state"] == "INTENT_CAPTURE"

    # 4. Ingest speech audio bytes
    audio_bytes = b"Is it going to rain in Punjab?"
    res_voice = await manager.handle_voice_recording("call-ivr-test", audio_bytes, "voice.wav")
    assert res_voice["success"] is True
    assert res_voice["current_state"] == "CONFIRMATION"

    # 5. Confirm and close (Press 1 to request summary & exit)
    res_exit = await manager.handle_dtmf_input("call-ivr-test", "1")
    assert res_exit["success"] is True
    assert res_exit["current_state"] == "EXIT"
    assert container.call_session_manager.get_session("call-ivr-test").state == CallSessionState.CLOSED
