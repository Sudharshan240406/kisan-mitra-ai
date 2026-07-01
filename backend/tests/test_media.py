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
from app.media.events import MediaEventType
from app.media.media import (
    DocumentProvider,
    DroneImageProvider,
    ImageProvider,
    MediaInput,
    MediaMetadata,
    MediaType,
    SensorProvider,
    VideoProvider,
    VoiceProvider,
)
from app.media.sessions import MediaSessionState


def test_media_providers_instantiation() -> None:
    # 1. Voice
    v = VoiceProvider("v1", "1.0.0", ["speech_to_text"])
    assert v.id == "v1"
    assert "speech_to_text" in v.capabilities

    # 2. Image
    img = ImageProvider("img1", "1.0.0", ["ocr"])
    assert img.id == "img1"

    # 3. Document
    doc = DocumentProvider("doc1", "1.0.0", ["parsing"])
    assert doc.id == "doc1"

    # 4. Sensor
    sns = SensorProvider("sns1", "1.0.0", ["anomaly_detection"])
    assert sns.id == "sns1"

    # 5. Drone
    dr = DroneImageProvider("dr1", "1.0.0", ["ndvi"])
    assert dr.id == "dr1"

    # 6. Video
    vid = VideoProvider("vid1", "1.0.0", ["ffmpeg"])
    assert vid.id == "vid1"


@pytest.mark.asyncio
async def test_media_providers_processing() -> None:
    # Voice STT process test
    v = VoiceProvider("v1", "1.0.0", ["speech_to_text"])
    inp = MediaInput(
        media_type=MediaType.VOICE,
        filename="query.wav",
        content=b"What is wheat price?",
        metadata=MediaMetadata(file_size_bytes=20, format="wav")
    )
    res = await v.process(inp)
    assert res.success is True
    assert res.extracted_text == "What is wheat price?"

    # Image anomaly detection
    img = ImageProvider("img1")
    inp_img = MediaInput(
        media_type=MediaType.IMAGE,
        filename="rust.png",
        content=b"Leaf rust disease scan",
        metadata=MediaMetadata(file_size_bytes=22, format="png")
    )
    res_img = await img.process(inp_img)
    assert res_img.success is True
    assert "rust" in res_img.classification_tags
    assert len(res_img.anomalies) > 0

    # Sensor dry anomaly detection
    sns = SensorProvider("sns1")
    inp_sns = MediaInput(
        media_type=MediaType.SENSOR,
        filename="moisture.csv",
        content=b"moisture:10%",
        metadata=MediaMetadata(file_size_bytes=12, format="csv")
    )
    res_sns = await sns.process(inp_sns)
    assert res_sns.success is True
    assert len(res_sns.anomalies) == 1
    assert "moisture" in res_sns.anomalies[0].lower()


@pytest.mark.asyncio
async def test_media_provider_registry() -> None:
    container = Container()
    registry = container.media_provider_registry

    # Discover default loaded providers
    voice_mock = registry.discover("voice-mock")
    assert voice_mock is not None
    assert voice_mock.id == "voice-mock"

    # Discover by type
    voice_providers = registry.discover_by_type(MediaType.VOICE)
    assert len(voice_providers) == 1
    assert voice_providers[0].id == "voice-mock"

    # Validate dependencies
    assert registry.validate_dependencies("voice-mock") is True

    # Health check
    health = await registry.health_check()
    assert health["voice-mock"]["healthy"] is True

    # Load from configs
    configs = [
        {"provider_id": "cfg-voice", "media_type": "voice", "version": "1.0.0", "capabilities": ["speech"]},
        {"provider_id": "invalid-cfg", "version": "1.0.0"}  # missing media_type
    ]
    registry.load_from_config(configs)
    assert registry.discover("cfg-voice") is not None
    assert registry.discover("invalid-cfg") is None


@pytest.mark.asyncio
async def test_media_sessions() -> None:
    container = Container()
    sm = container.media_session_manager

    events_logged = []
    def track_events(event: Any) -> None:
        events_logged.append(event)
    container.event_bus.subscribe("media_session_started", track_events)
    container.event_bus.subscribe("media_session_ended", track_events)

    # Create session
    sess = sm.create_session("conv-123", "voice", timeout_seconds=10)
    assert sess.state == MediaSessionState.ACTIVE
    assert sess.conversation_id == "conv-123"
    assert len(events_logged) == 1
    assert events_logged[0].event_type == "media_session_started"

    # Get session
    retrieved = sm.get_session(sess.media_session_id)
    assert retrieved is not None
    assert retrieved.media_session_id == sess.media_session_id

    # Touch test
    original_last_activity = retrieved.last_activity
    time.sleep(0.01)
    retrieved.touch()
    assert retrieved.last_activity > original_last_activity

    # Timeout Expiry
    sess.timeout_seconds = 0
    time.sleep(0.001)
    assert sess.is_expired() is True
    assert sm.get_session(sess.media_session_id).state == MediaSessionState.EXPIRED

    # Recovery
    recovered = sm.recover_session(sess.media_session_id)
    assert recovered.state == MediaSessionState.RECOVERED
    assert recovered.recovery_count == 1

    # Close session
    sm.close_session(sess.media_session_id)
    assert sm.get_session(sess.media_session_id).state == MediaSessionState.CLOSED
    assert len(events_logged) == 2
    assert events_logged[1].event_type == "media_session_ended"


@pytest.mark.asyncio
async def test_media_pipeline_validation_and_errors() -> None:
    container = Container()
    pipeline = container.media_pipeline

    # 1. Unsupported type format rejection
    invalid_input = MediaInput(
        media_type=MediaType.VOICE,
        filename="file.txt",  # Unsupported format for voice
        content=b"hello",
        metadata=MediaMetadata(file_size_bytes=5, format="txt")
    )
    res = await pipeline.execute(invalid_input, "conv-valid")
    assert res["success"] is False
    assert res["status"] == "rejected"
    assert "Format" in res["errors"][0]

    # 2. Oversized file rejection (Limit 20MB)
    oversized_input = MediaInput(
        media_type=MediaType.VOICE,
        filename="voice.wav",
        content=b"hello",
        metadata=MediaMetadata(file_size_bytes=21 * 1024 * 1024, format="wav")
    )
    res_size = await pipeline.execute(oversized_input, "conv-valid")
    assert res_size["success"] is False
    assert "exceeds" in res_size["errors"][0]


@pytest.mark.asyncio
async def test_media_pipeline_complete_routing_and_policy() -> None:
    container = Container()
    pipeline = container.media_pipeline

    # Subscribe to EventBus MIP events
    events_logged = {}
    def track_mip_event(event: Any) -> None:
        events_logged[event.event_type] = event

    for evt in [
        MediaEventType.MEDIA_RECEIVED,
        MediaEventType.MEDIA_VALIDATED,
        MediaEventType.MEDIA_PROCESSED,
        MediaEventType.PROCESSING_COMPLETED,
        MediaEventType.MEDIA_REJECTED
    ]:
        container.event_bus.subscribe(evt.value, track_mip_event)

    # Register all platform agents so orchestrator executes cleanly
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

    # Connect a mock WebChat channel to allow orchestrator to deliver standard responses
    from app.channels.channels import ChannelMetadata, ChannelType, WebChatChannel
    web_meta = ChannelMetadata(channel_id="web-001", channel_type=ChannelType.WEB_CHAT, name="Web Chat")
    web_ch = WebChatChannel(web_meta)
    container.channel_registry.register(web_ch)

    # 1. Happy path: voice query processes and invokes orchestrator successfully
    voice_input = MediaInput(
        media_type=MediaType.VOICE,
        filename="voice.wav",
        content=b"What is the recommended fertilizer for wheat crops in Punjab?",
        metadata=MediaMetadata(file_size_bytes=100, format="wav")
    )
    res = await pipeline.execute(voice_input, "conv-999")
    assert res["success"] is True
    assert res["status"] == "completed"
    assert res["media_result"].success is True
    assert "fertilizer" in res["media_result"].extracted_text

    # Verify EventBus MIP events published
    assert MediaEventType.MEDIA_RECEIVED.value in events_logged
    assert MediaEventType.MEDIA_VALIDATED.value in events_logged
    assert MediaEventType.MEDIA_PROCESSED.value in events_logged
    assert MediaEventType.PROCESSING_COMPLETED.value in events_logged

    # Verify Telemetry compiled
    metrics = container.telemetry.export_metrics()
    assert "media_metrics" in metrics
    assert "multimodal_metrics" in metrics
    assert metrics["media_metrics"]["total_processed"] == 1
    assert metrics["media_metrics"]["avg_processing_latency_ms"] > 0
    assert metrics["media_metrics"]["media_utilization"]["voice"] == 1
    assert metrics["voice_metrics"]["total_sessions"] == 1
    assert res["reasoning_result"].overall_confidence > 0

    # 2. Policy violation path: voice query containing unapproved keywords gets rejected
    events_logged.clear()
    policy_violation_input = MediaInput(
        media_type=MediaType.VOICE,
        filename="voice.wav",
        content=b"Use illegal pesticide to clear the worms.",
        metadata=MediaMetadata(file_size_bytes=100, format="wav")
    )
    res_policy = await pipeline.execute(policy_violation_input, "conv-999")
    assert res_policy["success"] is False
    assert res_policy["status"] == "rejected"
    assert any("illegal pesticide" in err.lower() for err in res_policy["errors"])

    # Verify MediaRejected event triggered
    assert MediaEventType.MEDIA_REJECTED.value in events_logged

    # Verify Telemetry metrics recorded violation
    metrics_violation = container.telemetry.export_metrics()
    assert metrics_violation["media_metrics"]["policy_violations"] == 1
