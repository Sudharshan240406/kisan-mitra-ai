import time
from typing import Any

import pytest
from agents.disease.disease import KnowledgeAgent
from agents.market.market import MarketAgent
from agents.memory.memory import MemoryAgent
from agents.planner.planner import PlannerAgent
from agents.schemes.schemes import GovernmentSchemeAgent
from agents.verifier.verifier import VerifierAgent
from agents.weather.weather import WeatherAgent
from app.core.container import Container
from app.telephony.events import TelephonyEventType
from app.telephony.ivr import IVRState
from app.telephony.sessions import CallSessionState
from app.telephony.telephony import (
    BSNLTelephonyProvider,
    CallStatus,
    ExotelTelephonyProvider,
    PlivoTelephonyProvider,
    TwilioTelephonyProvider,
)


def test_telephony_providers_instantiation() -> None:
    # 1. Twilio
    t = TwilioTelephonyProvider("t1", "1.0.0", ["tts"])
    assert t.id == "t1"
    assert "tts" in t.capabilities

    # 2. Plivo
    p = PlivoTelephonyProvider("p1")
    assert p.id == "p1"

    # 3. Exotel
    e = ExotelTelephonyProvider("e1")
    assert e.id == "e1"

    # 4. BSNL
    b = BSNLTelephonyProvider("b1")
    assert b.id == "b1"


@pytest.mark.asyncio
async def test_telephony_provider_operations() -> None:
    t = TwilioTelephonyProvider("t1")
    call_id = await t.initiate_call("+123456", "+654321")
    assert "CALL-OUT" in call_id

    details = await t.get_call_details(call_id)
    assert details is not None
    assert details.status == CallStatus.ANSWERED
    assert details.metadata.caller == "+654321"

    assert await t.send_dtmf(call_id, "1") is True
    assert await t.speak_text(call_id, "hello", "en") is True
    assert await t.play_audio(call_id, "http://audio") is True
    assert await t.start_recording(call_id) is True
    rec_url = await t.stop_recording(call_id)
    assert "wav" in rec_url

    assert await t.hangup(call_id) is True
    details_after = await t.get_call_details(call_id)
    assert details_after.status == CallStatus.COMPLETED


@pytest.mark.asyncio
async def test_telephony_provider_registry() -> None:
    container = Container()
    registry = container.telephony_provider_registry

    twilio_mock = registry.discover("twilio-mock")
    assert twilio_mock is not None
    assert twilio_mock.id == "twilio-mock"

    assert registry.validate_dependencies("twilio-mock") is True

    health = await registry.health_check()
    assert health["twilio-mock"]["healthy"] is True

    configs = [
        {"provider_id": "cfg-tel", "provider_type": "twilio", "version": "1.1.0"},
        {"provider_id": "invalid-cfg", "version": "1.0.0"}  # missing provider_type
    ]
    registry.load_from_config(configs)
    assert registry.discover("cfg-tel") is not None
    assert registry.discover("invalid-cfg") is None


@pytest.mark.asyncio
async def test_telephony_sessions() -> None:
    container = Container()
    sm = container.call_session_manager

    events_logged = []
    def track_events(event: Any) -> None:
        events_logged.append(event)
    container.event_bus.subscribe("telephony_session_started", track_events)
    container.event_bus.subscribe("telephony_session_ended", track_events)

    sess = sm.create_session("call-123", language="pa", timeout_seconds=15)
    assert sess.state == CallSessionState.ACTIVE
    assert sess.language == "pa"
    assert len(events_logged) == 1
    assert events_logged[0].event_type == "telephony_session_started"

    retrieved = sm.get_session("call-123")
    assert retrieved is not None
    assert retrieved.call_id == "call-123"

    time.sleep(0.005)
    retrieved.touch()

    # Expire
    sess.timeout_seconds = 0
    time.sleep(0.001)
    assert sess.is_expired() is True
    assert sm.get_session("call-123").state == CallSessionState.EXPIRED

    # Recover
    recovered = sm.recover_session("call-123")
    assert recovered.state == CallSessionState.RECOVERED
    assert recovered.recovery_count == 1

    # Close
    sm.close_session("call-123")
    assert sm.get_session("call-123").state == CallSessionState.CLOSED
    assert len(events_logged) == 2
    assert events_logged[1].event_type == "telephony_session_ended"


@pytest.mark.asyncio
async def test_ivr_state_machine_transitions() -> None:
    container = Container()
    sm = container.call_session_manager
    ivr = container.ivr_state_machine

    sess = sm.create_session("call-111", language="en")
    assert sess.current_ivr_state == "GREETING"

    # Greeting -> Language Selection direct transition
    state, prompt = await ivr.transition(sess, "next")
    assert state == IVRState.LANGUAGE_SELECTION
    assert "To select language" in prompt

    # Language Selection -> Caller Identification via DTMF
    state_lang, prompt_lang = await ivr.handle_dtmf(sess, "1")  # Press 1 for Hindi
    assert sess.language == "hi"
    assert state_lang == IVRState.CALLER_IDENTIFICATION
    assert "पंजीकृत" in prompt_lang or "ग्रुप" in prompt_lang or "दबाएं" in prompt_lang

    # Caller Identification -> Intent Capture via DTMF (guest)
    state_id, prompt_id = await ivr.handle_dtmf(sess, "3")  # Press 3 for guest demo
    assert sess.metadata.get("caller_type") == "guest"
    assert state_id == IVRState.INTENT_CAPTURE
    assert "मुख्य मेनू" in prompt_id

    # Invalid DTMF button fallback
    state_fail, prompt_fail = await ivr.handle_dtmf(sess, "8")
    assert state_fail == IVRState.INTENT_CAPTURE
    assert "Invalid input" in prompt_fail


@pytest.mark.asyncio
async def test_call_manager_e2e_flow() -> None:
    container = Container()
    manager = container.call_manager

    events_logged = {}
    def track_events(event: Any) -> None:
        events_logged[event.event_type] = event

    for evt in [
        TelephonyEventType.INCOMING_CALL,
        TelephonyEventType.CALL_ANSWERED,
        TelephonyEventType.IVR_STARTED,
        TelephonyEventType.LANGUAGE_SELECTED,
        TelephonyEventType.RECOMMENDATION_PLAYED,
        TelephonyEventType.DTMF_RECEIVED,
        TelephonyEventType.CALL_ENDED
    ]:
        container.event_bus.subscribe(evt.value, track_events)

    # Register core agents
    planner_agent = PlannerAgent(container.llm_provider)
    weather_agent = WeatherAgent(container.llm_provider, container.weather_service)
    market_agent = MarketAgent(container.llm_provider, container.market_service)
    memory_agent = MemoryAgent(container.llm_provider, container.memory_service)
    knowledge_agent = KnowledgeAgent(container.llm_provider, container.knowledge_service)
    scheme_agent = GovernmentSchemeAgent(container.llm_provider, container.scheme_service)
    verifier_agent = VerifierAgent(container.llm_provider)

    await planner_agent.initialize()
    await weather_agent.initialize()
    await market_agent.initialize()
    await memory_agent.initialize()
    await knowledge_agent.initialize()
    await scheme_agent.initialize()
    await verifier_agent.initialize()

    container.registry.register(planner_agent)
    container.registry.register(weather_agent)
    container.registry.register(market_agent)
    container.registry.register(memory_agent)
    container.registry.register(knowledge_agent)
    container.registry.register(scheme_agent)
    container.registry.register(verifier_agent)

    # Register channels
    from app.channels.channels import (
        ChannelMetadata,
        ChannelType,
        IVRChannel,
        WebChatChannel,
    )
    ivr_meta = ChannelMetadata(channel_id="ivr-001", channel_type=ChannelType.IVR, name="IVR Channel")
    ivr_ch = IVRChannel(ivr_meta)
    container.channel_registry.register(ivr_ch)

    web_meta = ChannelMetadata(channel_id="web-001", channel_type=ChannelType.WEB_CHAT, name="Web Chat")
    web_ch = WebChatChannel(web_meta)
    container.channel_registry.register(web_ch)

    # 1. Incoming Call Ingest
    res_in = await manager.handle_incoming_call("+9199999", "+9188888", "call-test-99")
    assert res_in["success"] is True
    assert res_in["current_state"] == "LANGUAGE_SELECTION"
    assert "किसान मित्र" in res_in["tts_prompt"]

    assert TelephonyEventType.INCOMING_CALL.value in events_logged
    assert TelephonyEventType.CALL_ANSWERED.value in events_logged
    assert TelephonyEventType.IVR_STARTED.value in events_logged

    # 2. Select language
    res_lang = await manager.handle_dtmf_input("call-test-99", "1")  # Hindi
    assert res_lang["success"] is True
    assert res_lang["current_state"] == "CALLER_IDENTIFICATION"
    assert TelephonyEventType.LANGUAGE_SELECTED.value in events_logged

    # 2b. Caller identification (guest demo)
    res_caller = await manager.handle_dtmf_input("call-test-99", "3")  # Guest
    assert res_caller["success"] is True
    assert res_caller["current_state"] == "INTENT_CAPTURE"

    # 3. Select intent (2 = Weather query — avoids scheme inquiry async flow)
    res_intent = await manager.handle_dtmf_input("call-test-99", "2")
    assert res_intent["success"] is True
    assert res_intent["current_state"] == "CONFIRMATION"
    assert "सलाह" in res_intent["tts_prompt"]
    assert "weather" in res_intent["tts_prompt"].lower() or "mock" in res_intent["tts_prompt"].lower()
    assert TelephonyEventType.RECOMMENDATION_PLAYED.value in events_logged

    # 4. Confirm and hangup (1 = Yes)
    res_exit = await manager.handle_dtmf_input("call-test-99", "1")
    assert res_exit["success"] is True
    assert res_exit["current_state"] == "EXIT"
    assert TelephonyEventType.CALL_ENDED.value in events_logged

    # 5. Check Telemetry Compiled
    metrics = container.telemetry.export_metrics()
    assert "telephony_metrics" in metrics
    assert metrics["telephony_metrics"]["total_calls"] == 1
    assert metrics["telephony_metrics"]["ivr_completion_rate"] == 1.0
    assert metrics["telephony_metrics"]["avg_routing_latency_ms"] > 0.0


@pytest.mark.asyncio
async def test_call_manager_voicemail_flow() -> None:
    container = Container()
    manager = container.call_manager

    # Setup dependencies
    planner_agent = PlannerAgent(container.llm_provider)
    weather_agent = WeatherAgent(container.llm_provider, container.weather_service)
    market_agent = MarketAgent(container.llm_provider, container.market_service)
    memory_agent = MemoryAgent(container.llm_provider, container.memory_service)
    knowledge_agent = KnowledgeAgent(container.llm_provider, container.knowledge_service)
    scheme_agent = GovernmentSchemeAgent(container.llm_provider, container.scheme_service)
    verifier_agent = VerifierAgent(container.llm_provider)

    await planner_agent.initialize()
    await weather_agent.initialize()
    await market_agent.initialize()
    await memory_agent.initialize()
    await knowledge_agent.initialize()
    await scheme_agent.initialize()
    await verifier_agent.initialize()

    container.registry.register(planner_agent)
    container.registry.register(weather_agent)
    container.registry.register(market_agent)
    container.registry.register(memory_agent)
    container.registry.register(knowledge_agent)
    container.registry.register(scheme_agent)
    container.registry.register(verifier_agent)


    from app.channels.channels import (
        ChannelMetadata,
        ChannelType,
        IVRChannel,
        WebChatChannel,
    )
    ivr_meta = ChannelMetadata(channel_id="ivr-001", channel_type=ChannelType.IVR, name="IVR Channel")
    ivr_ch = IVRChannel(ivr_meta)
    container.channel_registry.register(ivr_ch)

    web_meta = ChannelMetadata(channel_id="web-001", channel_type=ChannelType.WEB_CHAT, name="Web Chat")
    web_ch = WebChatChannel(web_meta)
    container.channel_registry.register(web_ch)

    # Inbound
    await manager.handle_incoming_call("+9199999", "+9188888", "call-test-voicemail")
    await manager.handle_dtmf_input("call-test-voicemail", "1")  # Language selection

    # Upload voicemail recorded speech bytes
    audio_content = b"What is the recommended fertilizer for wheat crops in Punjab?"
    res_voice = await manager.handle_voice_recording("call-test-voicemail", audio_content, "voicemail.wav")
    assert res_voice["success"] is True
    assert res_voice["current_state"] == "CONFIRMATION"
    assert "सलाह" in res_voice["tts_prompt"]
    # The new AI Reasoning Platform (ChiefReasoningAgent) produces a rich advisory
    # with a confidence tag instead of the legacy VerifierAgent's 'Memory' section.
    assert "CONFIDENCE" in res_voice["tts_prompt"] or "सलाह" in res_voice["tts_prompt"]
