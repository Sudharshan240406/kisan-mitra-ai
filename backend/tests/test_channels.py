import asyncio
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
from app.channels.channels import (
    ChannelMetadata,
    ChannelStatus,
    ChannelType,
    IVRChannel,
    MobileAppChannel,
    SMSChannel,
    VoiceChannel,
    WebChatChannel,
    WhatsAppChannel,
)
from app.channels.envelope import (
    LanguageMetadata,
    MessageEnvelope,
    MessagePriority,
    ResponseEnvelope,
)
from app.channels.events import ChannelEventType
from app.channels.sessions import SessionState
from app.core.container import Container


def test_channel_framework_instantiation() -> None:
    # 1. Voice Channel
    voice_meta = ChannelMetadata(
        channel_id="voice-01",
        channel_type=ChannelType.VOICE,
        name="Mock Voice Gateway",
        capabilities=["voice_call", "bi-directional_audio"],
        supported_media=["audio"]
    )
    voice_ch = VoiceChannel(voice_meta)
    assert voice_ch.channel_metadata.channel_type == ChannelType.VOICE
    assert "voice_call" in voice_ch.channel_metadata.capabilities

    # 2. SMS Channel
    sms_meta = ChannelMetadata(
        channel_id="sms-01",
        channel_type=ChannelType.SMS,
        name="Mock SMS Gateway",
        capabilities=["sms_text"],
        supported_media=["text"]
    )
    sms_ch = SMSChannel(sms_meta)
    assert sms_ch.channel_metadata.channel_type == ChannelType.SMS

    # 3. IVR Channel
    ivr_meta = ChannelMetadata(
        channel_id="ivr-01",
        channel_type=ChannelType.IVR,
        name="Mock IVR Menu",
        capabilities=["voice_menu", "dtmf"],
        supported_media=["audio"]
    )
    ivr_ch = IVRChannel(ivr_meta)
    assert ivr_ch.channel_metadata.channel_type == ChannelType.IVR

    # 4. WhatsApp Channel
    wa_meta = ChannelMetadata(
        channel_id="wa-01",
        channel_type=ChannelType.WHATSAPP,
        name="Mock WhatsApp Business",
        capabilities=["rich_messaging"],
        supported_media=["text", "image"]
    )
    wa_ch = WhatsAppChannel(wa_meta)
    assert wa_ch.channel_metadata.channel_type == ChannelType.WHATSAPP

    # 5. Mobile App Channel
    mob_meta = ChannelMetadata(
        channel_id="mob-01",
        channel_type=ChannelType.MOBILE_APP,
        name="Mock Mobile App",
        capabilities=["push_notifications"],
        supported_media=["text"]
    )
    mob_ch = MobileAppChannel(mob_meta)
    assert mob_ch.channel_metadata.channel_type == ChannelType.MOBILE_APP

    # 6. Web Chat Channel
    web_meta = ChannelMetadata(
        channel_id="web-01",
        channel_type=ChannelType.WEB_CHAT,
        name="Mock Web Chat",
        capabilities=["markdown"],
        supported_media=["text"]
    )
    web_ch = WebChatChannel(web_meta)
    assert web_ch.channel_metadata.channel_type == ChannelType.WEB_CHAT


@pytest.mark.asyncio
async def test_channel_send_receive_health() -> None:
    meta = ChannelMetadata(
        channel_id="test-ch",
        channel_type=ChannelType.WEB_CHAT,
        name="Test Channel",
        status=ChannelStatus.ACTIVE
    )
    channel = WebChatChannel(meta)

    # Test health check
    assert await channel.health_check() is True

    # Test send
    payload = {"text": "hello"}
    success = await channel.send("user1", payload)
    assert success is True
    assert channel._sent_messages[0] == ("user1", payload)

    # Test receive
    assert await channel.receive() is None
    channel.enqueue_received(payload)
    received = await channel.receive()
    assert received == payload
    assert await channel.receive() is None

    # Test unhealthy status
    channel.channel_metadata.status = ChannelStatus.INACTIVE
    assert await channel.health_check() is False


@pytest.mark.asyncio
async def test_channel_registry() -> None:
    container = Container()
    registry = container.channel_registry

    events_logged = []
    def event_handler(event: Any) -> None:
        events_logged.append(event)
    container.event_bus.subscribe(ChannelEventType.CHANNEL_CONNECTED.value, event_handler)
    container.event_bus.subscribe(ChannelEventType.CHANNEL_DISCONNECTED.value, event_handler)

    meta = ChannelMetadata(
        channel_id="voice-01",
        channel_type=ChannelType.VOICE,
        name="Mock Voice",
        capabilities=["voice_call"],
        version="2.1.0"
    )
    ch = VoiceChannel(meta)

    # Register
    registry.register(ch)
    assert registry.discover("voice-01") == ch
    assert len(registry.list_channels()) == 1
    assert len(registry.discover_by_type(ChannelType.VOICE)) == 1
    assert len(registry.discover_by_capability("voice_call")) == 1
    assert registry.get_channel_versions()["voice-01"] == "2.1.0"
    assert len(events_logged) == 1
    assert events_logged[0].event_type == ChannelEventType.CHANNEL_CONNECTED.value
    assert events_logged[0].payload["channel_id"] == "voice-01"

    # Dependency validation
    assert registry.validate_dependencies("voice-01") is True

    # WhatsApp missing api_endpoint validation
    wa_meta = ChannelMetadata(
        channel_id="wa-01",
        channel_type=ChannelType.WHATSAPP,
        name="Mock WhatsApp"
    )
    wa_ch = WhatsAppChannel(wa_meta)
    registry.register(wa_ch)
    assert registry.validate_dependencies("wa-01") is False  # Needs api_endpoint

    wa_ch.channel_metadata.metadata["api_endpoint"] = "https://wa.api"
    assert registry.validate_dependencies("wa-01") is True

    # Load from config
    configs = [
        {"channel_id": "sms-cfg", "channel_type": "sms", "name": "SMS Configured", "status": "active"},
        {"channel_id": "invalid-cfg", "channel_type": "sms"}  # missing name
    ]
    registry.load_from_config(configs)
    assert registry.discover("sms-cfg") is not None
    assert registry.discover("invalid-cfg") is None
    assert registry.discover("sms-cfg").channel_metadata.channel_type == ChannelType.SMS

    # Deregister
    registry.deregister("voice-01")
    assert registry.discover("voice-01") is None
    assert len(events_logged) == 4
    assert events_logged[3].event_type == ChannelEventType.CHANNEL_DISCONNECTED.value


@pytest.mark.asyncio
async def test_session_manager() -> None:
    container = Container()
    sm = container.session_manager

    events_logged = []
    def event_handler(event: Any) -> None:
        events_logged.append(event)
    container.event_bus.subscribe(ChannelEventType.SESSION_STARTED.value, event_handler)
    container.event_bus.subscribe(ChannelEventType.SESSION_ENDED.value, event_handler)
    container.event_bus.subscribe(ChannelEventType.SESSION_EXPIRED.value, event_handler)
    container.event_bus.subscribe(ChannelEventType.SESSION_RECOVERED.value, event_handler)

    # 1. Custom defaults for timeouts
    voice_sess = sm.create_session("conv-1", "voice-01", "voice")
    assert voice_sess.timeout_seconds == 300  # 5 min

    sms_sess = sm.create_session("conv-2", "sms-01", "sms")
    assert sms_sess.timeout_seconds == 86400  # 24 hrs

    default_sess = sm.create_session("conv-3", "web-01", "web_chat")
    assert default_sess.timeout_seconds == 1800  # 30 min

    assert len(events_logged) == 3
    assert events_logged[0].event_type == ChannelEventType.SESSION_STARTED.value

    # 2. Get and Touch
    sess = sm.get_session(voice_sess.session_id)
    assert sess is not None
    assert sess.state == SessionState.ACTIVE

    # Touch test
    original_last_activity = sess.last_activity
    time.sleep(0.01)
    sess.touch()
    assert sess.last_activity > original_last_activity

    # 3. Expiration & Cleanup
    sess.timeout_seconds = 0  # Force immediate timeout
    time.sleep(0.001)
    assert sess.is_expired() is True

    # get_session marks it expired
    assert sm.get_session(sess.session_id).state == SessionState.EXPIRED

    # 4. Recover session
    recovered = sm.recover_session(sess.session_id)
    assert recovered.state == SessionState.RECOVERED
    assert recovered.timeout_seconds == 0
    recovered.timeout_seconds = 100
    assert recovered.is_expired() is False

    # 5. Close session
    sm.close_session(voice_sess.session_id)
    assert sm.get_session(voice_sess.session_id).state == SessionState.CLOSED

    # 6. Cleanup expired
    sms_sess.timeout_seconds = 0
    time.sleep(0.001)
    expired_count = sm.cleanup_expired()
    assert expired_count == 1
    assert sm.get_session(sms_sess.session_id).state == SessionState.EXPIRED


def test_message_envelope_creation() -> None:
    lang = LanguageMetadata(
        preferred_language="hi",
        locale="hi-IN",
        region="IN",
        script="Devanagari",
        future_translation_enabled=True
    )
    envelope = MessageEnvelope(
        conversation_id="conv-123",
        channel="sms-01",
        sender="farmer-456",
        language=lang,
        payload={"text": "How to treat wheat rust?"},
        priority=MessagePriority.URGENT,
        correlation_id="corr-abc",
        trace_id="tr-xyz"
    )

    assert envelope.conversation_id == "conv-123"
    assert envelope.language.preferred_language == "hi"
    assert envelope.priority == MessagePriority.URGENT
    assert envelope.correlation_id == "corr-abc"
    assert envelope.trace_id == "tr-xyz"

    response = ResponseEnvelope(
        message_id=envelope.message_id,
        conversation_id="conv-123",
        channel="sms-01",
        receiver="farmer-456",
        language=lang,
        payload={"recommendation": "Use fungicide X."},
        trace_id="tr-xyz",
        status="success"
    )

    assert response.message_id == envelope.message_id
    assert response.payload["recommendation"] == "Use fungicide X."


@pytest.mark.asyncio
async def test_routers_and_telemetry_workflow() -> None:
    container = Container()

    # Subscribe to events to verify Router publishes
    events_logged = {}
    def track_event(event: Any) -> None:
        events_logged[event.event_type] = event

    for evt in [
        ChannelEventType.MESSAGE_RECEIVED,
        ChannelEventType.MESSAGE_PROCESSED,
        ChannelEventType.RESPONSE_GENERATED,
        ChannelEventType.RESPONSE_DELIVERED,
        ChannelEventType.ERROR_OCCURRED
    ]:
        container.event_bus.subscribe(evt.value, track_event)

    # 1. Reject invalid envelope
    invalid_envelope = MessageEnvelope(
        conversation_id="",  # Invalid
        channel="sms-01",
        sender="",  # Invalid
        payload={"text": "hello"}
    )
    rejected_res = await container.channel_router.route_inbound(invalid_envelope)
    assert rejected_res.status == "rejected"
    assert "error_occurred" in events_logged

    # 2. Reject unregistered channel
    unregistered_envelope = MessageEnvelope(
        conversation_id="conv-999",
        channel="unknown-ch",
        sender="farmer-999",
        payload={"text": "hello"}
    )
    rejected_res2 = await container.channel_router.route_inbound(unregistered_envelope)
    assert rejected_res2.status == "rejected"

    # Register actual channel
    meta = ChannelMetadata(
        channel_id="sms-01",
        channel_type=ChannelType.SMS,
        name="Test SMS Gateway"
    )
    sms_ch = SMSChannel(meta)
    container.channel_registry.register(sms_ch)

    # We need to register agents so the orchestrator inside route_inbound can resolve
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

    # 3. Synchronous inbound route
    valid_envelope = MessageEnvelope(
        conversation_id="conv-111",
        channel="sms-01",
        sender="farmer-111",
        payload={"text": "Market price of wheat?"}
    )

    response_env = await container.channel_router.route_inbound(valid_envelope, asynchronous=False)
    assert response_env.status == "success"
    assert response_env.channel == "sms-01"
    assert response_env.receiver == "farmer-111"

    # Verify event types published
    assert ChannelEventType.MESSAGE_RECEIVED.value in events_logged
    assert ChannelEventType.MESSAGE_PROCESSED.value in events_logged
    assert ChannelEventType.RESPONSE_GENERATED.value in events_logged
    assert ChannelEventType.RESPONSE_DELIVERED.value in events_logged

    # Verify telemetry aggregated
    metrics = container.telemetry.export_metrics()
    assert "channel_metrics" in metrics
    assert metrics["channel_metrics"]["messages_processed"] == 1
    assert metrics["channel_metrics"]["avg_routing_latency_ms"] > 0
    assert metrics["channel_metrics"]["channel_utilization"]["sms-01"] == 1

    # 4. Asynchronous inbound route
    events_logged.clear()
    async_envelope = MessageEnvelope(
        conversation_id="conv-222",
        channel="sms-01",
        sender="farmer-222",
        payload={"text": "Market price of wheat?"}
    )

    async_response = await container.channel_router.route_inbound(async_envelope, asynchronous=True)
    assert async_response.status == "queued"
    assert ChannelEventType.MESSAGE_RECEIVED.value in events_logged

    # Wait briefly for background task processing to complete
    await asyncio.sleep(0.5)

    # Verification of background run completion
    assert ChannelEventType.MESSAGE_PROCESSED.value in events_logged
    metrics_updated = container.telemetry.export_metrics()
    assert metrics_updated["channel_metrics"]["messages_processed"] == 2


@pytest.mark.asyncio
async def test_telemetry_router_metrics() -> None:
    from app.api.v1.telemetry import get_telemetry_metrics
    container = Container()
    metrics = await get_telemetry_metrics(container)
    assert "channel_metrics" in metrics
    assert "media_metrics" in metrics
    assert "telephony_metrics" in metrics
    assert "sms_metrics" in metrics

