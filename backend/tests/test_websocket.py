"""
Phase 15 — WebSocket & IVR Enhancement Tests
===============================================
Tests WebSocket connection manager, error recovery, and IVR state machine.
"""
import pytest
from app.api.v1.websocket import ConnectionManager
from app.telephony.error_recovery import ErrorRecovery
from app.telephony.ivr import DEFAULT_IVR_CONFIG, IVRState, IVRStateMachine
from app.telephony.sessions import CallSession


class TestConnectionManager:
    """Tests for WebSocket connection manager."""

    def test_instantiation(self):
        manager = ConnectionManager()
        assert manager.client_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_no_clients(self):
        """Broadcasting with no clients should not raise."""
        manager = ConnectionManager()
        await manager.broadcast({"type": "TEST", "payload": {}})

    @pytest.mark.asyncio
    async def test_push_event(self):
        """Push event should not raise even with no clients."""
        manager = ConnectionManager()
        await manager.push_event("TEST_EVENT", {"key": "value"})


class TestErrorRecovery:
    """Tests for telephony error recovery."""

    def test_all_error_types_have_prompts(self):
        recovery = ErrorRecovery()
        error_types = ["no_speech", "poor_audio", "unknown_caller", "network_delay",
                       "no_schemes", "missing_info", "system_error", "timeout_warning"]
        for et in error_types:
            prompt_hi = recovery.get_recovery_prompt(et, "hi")
            prompt_en = recovery.get_recovery_prompt(et, "en")
            prompt_pa = recovery.get_recovery_prompt(et, "pa")
            assert len(prompt_hi) > 0, f"No Hindi prompt for {et}"
            assert len(prompt_en) > 0, f"No English prompt for {et}"
            assert len(prompt_pa) > 0, f"No Punjabi prompt for {et}"

    def test_should_retry(self):
        recovery = ErrorRecovery()
        assert recovery.should_retry(0) is True
        assert recovery.should_retry(2) is True
        assert recovery.should_retry(3) is False
        assert recovery.should_retry(5) is False

    def test_escalation_prompt(self):
        recovery = ErrorRecovery()
        prompt = recovery.get_escalation_prompt("hi")
        assert len(prompt) > 0
        prompt_en = recovery.get_escalation_prompt("en")
        assert "transfer" in prompt_en.lower() or "specialist" in prompt_en.lower()

    def test_classify_error_no_speech(self):
        recovery = ErrorRecovery()
        assert recovery.classify_error({"no_speech": True}) == "no_speech"

    def test_classify_error_unknown_caller(self):
        recovery = ErrorRecovery()
        assert recovery.classify_error({"unknown_caller": True}) == "unknown_caller"

    def test_classify_error_no_schemes(self):
        recovery = ErrorRecovery()
        assert recovery.classify_error({"no_schemes": True}) == "no_schemes"

    def test_classify_error_default(self):
        recovery = ErrorRecovery()
        assert recovery.classify_error({}) == "system_error"


class TestIVRStateMachine:
    """Tests for the enhanced IVR state machine."""

    def test_config_has_all_states(self):
        expected = [
            "GREETING", "LANGUAGE_SELECTION", "CALLER_IDENTIFICATION",
            "INTENT_CAPTURE", "SCHEME_INQUIRY", "SCHEME_RESULT",
            "DOCUMENT_ADVISOR", "CLARIFICATION", "RECOMMENDATION_PLAYBACK",
            "CONFIRMATION", "HUMAN_TRANSFER", "EXIT"
        ]
        for state in expected:
            assert state in DEFAULT_IVR_CONFIG, f"Missing state: {state}"

    @pytest.mark.asyncio
    async def test_greeting_prompt_exists(self):
        ivr = IVRStateMachine()
        prompt_hi = await ivr.get_prompt("GREETING", "hi")
        prompt_en = await ivr.get_prompt("GREETING", "en")
        assert len(prompt_hi) > 0
        assert len(prompt_en) > 0

    @pytest.mark.asyncio
    async def test_language_selection_prompt(self):
        ivr = IVRStateMachine()
        prompt = await ivr.get_prompt("LANGUAGE_SELECTION", "hi")
        assert "1" in prompt  # Press 1 for Hindi

    @pytest.mark.asyncio
    async def test_scheme_inquiry_prompt(self):
        ivr = IVRStateMachine()
        prompt = await ivr.get_prompt("SCHEME_INQUIRY", "hi")
        assert len(prompt) > 0

    @pytest.mark.asyncio
    async def test_dtmf_language_selection(self):
        ivr = IVRStateMachine()
        session = CallSession(call_id="TEST-001")
        session.current_ivr_state = "LANGUAGE_SELECTION"

        state, prompt = await ivr.handle_dtmf(session, "1")
        assert session.language == "hi"
        assert state == IVRState.CALLER_IDENTIFICATION

    @pytest.mark.asyncio
    async def test_dtmf_english_selection(self):
        ivr = IVRStateMachine()
        session = CallSession(call_id="TEST-002")
        session.current_ivr_state = "LANGUAGE_SELECTION"

        state, prompt = await ivr.handle_dtmf(session, "2")
        assert session.language == "en"

    @pytest.mark.asyncio
    async def test_dtmf_caller_identification(self):
        ivr = IVRStateMachine()
        session = CallSession(call_id="TEST-003")
        session.current_ivr_state = "CALLER_IDENTIFICATION"

        state, prompt = await ivr.handle_dtmf(session, "1")
        assert state == IVRState.INTENT_CAPTURE
        assert session.metadata.get("caller_type") == "registered"

    @pytest.mark.asyncio
    async def test_dtmf_scheme_intent(self):
        ivr = IVRStateMachine()
        session = CallSession(call_id="TEST-004")
        session.current_ivr_state = "INTENT_CAPTURE"

        state, prompt = await ivr.handle_dtmf(session, "1")
        assert state == IVRState.SCHEME_INQUIRY
        assert session.metadata.get("intent_query") == "government schemes eligibility"

    @pytest.mark.asyncio
    async def test_dtmf_weather_intent(self):
        ivr = IVRStateMachine()
        session = CallSession(call_id="TEST-005")
        session.current_ivr_state = "INTENT_CAPTURE"

        state, prompt = await ivr.handle_dtmf(session, "2")
        assert state == IVRState.RECOMMENDATION_PLAYBACK

    @pytest.mark.asyncio
    async def test_dtmf_human_transfer(self):
        ivr = IVRStateMachine()
        session = CallSession(call_id="TEST-006")
        session.current_ivr_state = "INTENT_CAPTURE"

        state, prompt = await ivr.handle_dtmf(session, "9")
        assert state == IVRState.HUMAN_TRANSFER

    @pytest.mark.asyncio
    async def test_dtmf_invalid_input_fallback(self):
        ivr = IVRStateMachine()
        session = CallSession(call_id="TEST-007")
        session.current_ivr_state = "INTENT_CAPTURE"

        state, prompt = await ivr.handle_dtmf(session, "7")
        # Should fallback to same state
        assert state == IVRState.INTENT_CAPTURE
        assert "Invalid" in prompt

    @pytest.mark.asyncio
    async def test_transition_from_greeting(self):
        ivr = IVRStateMachine()
        session = CallSession(call_id="TEST-008")
        session.current_ivr_state = "GREETING"

        state, prompt = await ivr.transition(session, "next")
        assert state == IVRState.LANGUAGE_SELECTION

    @pytest.mark.asyncio
    async def test_document_advisor_dtmf(self):
        ivr = IVRStateMachine()
        session = CallSession(call_id="TEST-009")
        session.current_ivr_state = "DOCUMENT_ADVISOR"

        state, prompt = await ivr.handle_dtmf(session, "9")
        assert state == IVRState.INTENT_CAPTURE

    def test_intent_menu_has_schemes(self):
        """Government schemes should be option 1 in the intent menu."""
        intent_config = DEFAULT_IVR_CONFIG["INTENT_CAPTURE"]
        dtmf_map = intent_config["dtmf"]
        assert "1" in dtmf_map
        assert dtmf_map["1"]["next"] == "SCHEME_INQUIRY"


class TestCallSessionFarmerFields:
    """Tests for farmer profile fields in CallSession."""

    def test_default_farmer_id_none(self):
        session = CallSession(call_id="TEST-010")
        assert session.farmer_id is None
        assert session.farmer_profile_snapshot == {}

    def test_set_farmer_id(self):
        session = CallSession(call_id="TEST-011")
        session.farmer_id = "DEMO-F001"
        session.farmer_profile_snapshot = {"name": "Ramesh Singh"}
        assert session.farmer_id == "DEMO-F001"
        assert session.farmer_profile_snapshot["name"] == "Ramesh Singh"
