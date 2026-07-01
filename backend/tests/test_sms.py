import pytest
from agents.planner.planner import PlannerAgent
from agents.verifier.verifier import VerifierAgent
from agents.weather.weather import WeatherAgent
from app.core.container import Container
from app.core.event_bus import Event
from app.sms.events import SMSEventType
from app.sms.sessions import SMSSessionManager, SMSSessionState
from app.sms.sms import SMSProviderRegistry, TwilioSMSProvider
from app.sms.templates import SMSTemplateEngine


@pytest.mark.asyncio
async def test_sms_provider_and_registry() -> None:
    registry = SMSProviderRegistry()
    provider = TwilioSMSProvider("test-twilio", "1.0.0", ["marketing"])
    registry.register(provider)

    assert registry.discover("test-twilio") == provider
    assert registry.validate_dependencies("test-twilio") is True

    providers = registry.list_providers()
    assert len(providers) == 1

    health = await registry.health_check()
    assert health["test-twilio"]["healthy"] is True

    registry.deregister("test-twilio")
    assert registry.discover("test-twilio") is None


@pytest.mark.asyncio
async def test_sms_session_manager() -> None:
    manager = SMSSessionManager()
    session = manager.create_session("+9199999", language="en")

    assert session.phone_number == "+9199999"
    assert session.language == "en"
    assert session.state == SMSSessionState.ACTIVE

    retrieved = manager.get_session(session.sms_session_id)
    assert retrieved == session

    by_phone = manager.get_session_by_phone("+9199999")
    assert by_phone == session

    # Expiry check
    session.timeout_seconds = -1  # force expire
    manager.cleanup_expired()
    assert session.state == SMSSessionState.EXPIRED

    # Recovery
    recovered = manager.recover_session(session.sms_session_id)
    assert recovered.state == SMSSessionState.RECOVERED
    assert recovered.retry_count == 1

    # Close
    manager.close_session(session.sms_session_id)
    assert session.state == SMSSessionState.CLOSED
    assert manager.get_session_by_phone("+9199999") is None


@pytest.mark.asyncio
async def test_sms_template_engine() -> None:
    engine = SMSTemplateEngine()

    # Hindi Government Scheme Alert template
    rendered_hi = engine.render(
        "gov_scheme",
        "hi",
        farmer_name="रवि",
        scheme_name="पीएम किसान",
        details="रु ६००० प्रति वर्ष"
    )
    assert "नमस्ते रवि" in rendered_hi
    assert "पीएम किसान" in rendered_hi

    # English Weather Alert template
    rendered_en = engine.render(
        "weather_alert",
        "en",
        region="Punjab",
        weather_condition="Heavy Rain",
        temp="24"
    )
    assert "Punjab" in rendered_en
    assert "Heavy Rain" in rendered_en


@pytest.mark.asyncio
async def test_sms_pipeline_governance_and_rate_limiting() -> None:
    container = Container()
    pipeline = container.sms_pipeline

    # 1. Sensitive Data scan rejection
    res_sensitive = await pipeline.execute("+9177777", "My credit card CVV is 123 and pin is 9999")
    assert res_sensitive["success"] is False
    assert "rejected" in res_sensitive["status"]
    assert any("sensitive" in err.lower() for err in res_sensitive["errors"])

    # 2. Oversized message warning rejection (>800 chars)
    oversized_text = "A" * 801
    res_oversized = await pipeline.execute("+9177777", oversized_text)
    assert res_oversized["success"] is False
    assert any("length" in err.lower() for err in res_oversized["errors"])

    # 3. Spam & Rate Limiter validation
    pipeline._rate_limiter._last_message.clear()
    pipeline._rate_limiter._history.clear()

    # Send same message rapidly (should block as duplicate)
    await pipeline.execute("+9188888", "Need weather updates")
    res_dup = await pipeline.execute("+9188888", "Need weather updates")
    assert res_dup["success"] is False
    assert any("duplicate" in err.lower() for err in res_dup["errors"])

    # Send different messages rapidly to trigger rate limit (max 5 request / min)
    pipeline._rate_limiter._last_message.clear()
    pipeline._rate_limiter._history.clear()

    for i in range(5):
        await pipeline.execute("+9199999", f"Unique request {i}")

    res_limit = await pipeline.execute("+9199999", "Sixth unique request")
    assert res_limit["success"] is False
    assert any("rate limit" in err.lower() for err in res_limit["errors"])


@pytest.mark.asyncio
async def test_sms_pipeline_end_to_end() -> None:
    container = Container()
    pipeline = container.sms_pipeline

    # Hook EventBus subscriber
    events_logged = []
    def log_events(event: Event) -> None:
        events_logged.append(event.event_type)

    for evt in SMSEventType:
        container.event_bus.subscribe(evt.value, log_events)

    # Register agents for orchestrator routing
    planner_agent = PlannerAgent(container.llm_provider)
    weather_agent = WeatherAgent(container.llm_provider, container.weather_service)
    verifier_agent = VerifierAgent(container.llm_provider)

    await planner_agent.initialize()
    await weather_agent.initialize()
    await verifier_agent.initialize()

    container.registry.register(planner_agent)
    container.registry.register(weather_agent)
    container.registry.register(verifier_agent)

    # Register channels
    from app.channels.channels import (
        ChannelMetadata,
        ChannelType,
        SMSChannel,
        WebChatChannel,
    )
    web_meta = ChannelMetadata(channel_id="web-001", channel_type=ChannelType.WEB_CHAT, name="Web")
    web_ch = WebChatChannel(web_meta)
    container.channel_registry.register(web_ch)

    sms_meta = ChannelMetadata(channel_id="sms-01", channel_type=ChannelType.SMS, name="SMS Channel")
    sms_ch = SMSChannel(sms_meta)
    container.channel_registry.register(sms_ch)

    # Execute Pipeline Inbound SMS
    res = await pipeline.execute("+9112345", "What is the weather in Khanna Punjab?")
    assert res["success"] is True
    assert res["delivery_status"] == "delivered"
    assert "Punjab" in res["rendered_reply"] or "मौसम" in res["rendered_reply"]


    # Event types logged checks
    assert SMSEventType.SMS_RECEIVED.value in events_logged
    assert SMSEventType.TEMPLATE_RENDERED.value in events_logged
    assert SMSEventType.SMS_SENT.value in events_logged
    assert SMSEventType.SMS_DELIVERED.value in events_logged

    # Telemetry checks
    metrics = container.telemetry.export_metrics()
    assert "sms_metrics" in metrics
    assert metrics["sms_metrics"]["received_count"] == 1
    assert metrics["sms_metrics"]["sent_count"] == 1
    assert metrics["sms_metrics"]["avg_processing_latency_ms"] > 0
    assert metrics["sms_metrics"]["language_distribution"]["hi"] == 1
