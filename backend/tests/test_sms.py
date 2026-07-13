from typing import Any

import pytest
from app.core.container import Container
from app.sms.exotel_provider import ExotelProvider
from app.sms.fallback_provider import FallbackProvider
from app.sms.inbound_router import InboundRouter
from app.sms.msg91_provider import MSG91Provider
from app.sms.provider_registry import ProviderRegistry
from app.sms.sms_manager import SMSManager
from app.sms.template_engine import TemplateEngine
from app.sms.twilio_provider import TwilioProvider


def test_sms_providers_instantiation() -> None:
    twilio = TwilioProvider()
    msg91 = MSG91Provider()
    exotel = ExotelProvider()
    fallback = FallbackProvider()

    assert twilio.id == "twilio"
    assert msg91.id == "msg91"
    assert exotel.id == "exotel"
    assert fallback.id == "fallback"


def test_provider_registry_operations() -> None:
    registry = ProviderRegistry()
    twilio = TwilioProvider()
    fallback = FallbackProvider()

    registry.register(twilio)
    registry.register(fallback)

    assert registry.discover("twilio") is twilio
    assert registry.discover("fallback") is fallback
    assert "twilio" in [p.id for p in registry.list_providers()]

    registry.set_active("fallback")
    assert registry.get_active() is fallback


def test_template_engine_substitutions() -> None:
    engine = TemplateEngine()

    # English v1 Weather Alert template test
    en_res = engine.render(
        template_key="weather_alert",
        language="en",
        version="v1",
        region="Punjab",
        weather_condition="Sunny",
        temp="35"
    )
    assert "Weather Alert: Punjab weather is Sunny (35C)." in en_res

    # Hindi v1 Gov Scheme template test
    hi_res = engine.render(
        template_key="gov_scheme",
        language="hi",
        version="v1",
        farmer_name="Ramesh",
        scheme_name="PM-Kisan",
        details="financial support"
    )
    assert "किसान मित्र: नमस्ते Ramesh, नई सरकारी योजना 'PM-Kisan' सक्रिय है।" in hi_res


@pytest.mark.asyncio
async def test_sms_manager_fallback_and_retry() -> None:
    registry = ProviderRegistry()

    # Setup failing provider
    failing_twilio = TwilioProvider(provider_id="twilio")
    async def fail_send(*args: Any, **kwargs: Any) -> bool:
        raise ValueError("Simulated network timeout")
    failing_twilio.send_sms = fail_send

    # Setup working provider
    working_fallback = FallbackProvider()

    registry.register(failing_twilio)
    registry.register(working_fallback)
    registry.set_active("twilio")

    manager = SMSManager(registry, TemplateEngine())

    # Send should succeed by falling back to working_fallback
    res = await manager.send_sms(recipient="+919876543210", body="Test retry alert")
    assert res is True


@pytest.mark.asyncio
async def test_inbound_router_two_way_flow() -> None:
    container = Container()
    router = InboundRouter(container)

    # Handle inbound message simulation
    reply = await router.handle_inbound_sms(sender="+919876543210", body="What is the weather?")
    assert len(reply) > 0


@pytest.mark.asyncio
async def test_ivr_summary_auto_sms() -> None:
    container = Container()

    # Verify manager and inbound router are mounted
    assert hasattr(container, "sms_manager")
    assert hasattr(container, "sms_inbound_router")

    # Setup call session
    session = container.call_session_manager.create_session(
        "call-sms-ivr-summary-test",
        language="hi",
        metadata={"caller": "+919876543210"}
    )

    # We navigate through the states to trigger summary
    from app.ivr.ivr_flow import IVRState
    session.current_ivr_state = IVRState.SUMMARY.value

    # Process DTMF key transition to EXIT which triggers summary & summary SMS
    from app.ivr.call_manager import CallManager
    call_mgr = CallManager(container)

    res = await call_mgr.handle_dtmf_input("call-sms-ivr-summary-test", "1")
    assert res["success"] is True

    # Wait for background SMS task to execute
    import asyncio
    await asyncio.sleep(0.1)

    # Verify SMS provider registered sent message
    sent = False
    for p in container.sms_provider_registry.list_providers():
        if hasattr(p, "_sent_messages") and len(p._sent_messages) > 0:
            sent = True
            break
    assert sent is True
