import pytest
from app.core.ai.adapters import GeminiAdapter
from app.core.ai.base import AICostLimitExceeded
from app.core.ai.cost_manager import CostAndPerformanceManager
from app.core.ai.platform import AIModelPlatform
from app.core.ai.registry import AIProviderRegistry
from app.core.ai.router import AIModelRouter
from app.core.event_bus import EventBus
from app.core.telemetry import TelemetryFramework


@pytest.fixture
def ai_setup():
    registry = AIProviderRegistry()
    cost_manager = CostAndPerformanceManager(registry, daily_budget_usd=2.0)
    router = AIModelRouter(registry)
    event_bus = EventBus()
    telemetry = TelemetryFramework()

    # Register mock adapters
    gemini = GeminiAdapter(api_key="mock-key", model_name="gemini-1.5-pro")
    openai = GeminiAdapter(api_key="mock-key", model_name="gpt-4o") # Mock wrapper reuse
    ollama = GeminiAdapter(api_key="mock-key", model_name="llama3")

    registry.register_adapter("gemini-1.5-pro", gemini)
    registry.register_adapter("gpt-4o", openai)
    registry.register_adapter("llama3", ollama)

    platform = AIModelPlatform(
        registry=registry,
        cost_manager=cost_manager,
        router=router,
        event_bus=event_bus,
        telemetry=telemetry
    )
    return {
        "registry": registry,
        "cost_manager": cost_manager,
        "router": router,
        "event_bus": event_bus,
        "platform": platform
    }

def test_registry_registration(ai_setup):
    reg = ai_setup["registry"]
    specs = reg.get_specs("gpt-4o")
    assert specs is not None
    assert specs.provider_name == "openai"
    assert "reasoning" in specs.capabilities

def test_cost_calculation(ai_setup):
    mgr = ai_setup["cost_manager"]
    cost = mgr.calculate_cost("gemini-1.5-pro", 200_000, 100_000)
    expected = (200_000 / 1_000_000.0) * 1.25 + (100_000 / 1_000_000.0) * 3.75
    assert cost == round(expected, 6)

def test_budget_cutoff_limit(ai_setup):
    mgr = ai_setup["cost_manager"]
    mgr.record_usage("gemini-1.5-pro", 1_000_000, 500_000) # Costs 1.25 + 1.875 = 3.125

    with pytest.raises(AICostLimitExceeded):
        mgr.check_budget_limits("gemini-1.5-pro", 10_000)

def test_router_mcda_scoring(ai_setup):
    router = ai_setup["router"]
    model_id, reason, confidence = router.select_model(
        task_type="reasoning",
        prompt_size=500,
        budget_remaining=2.0
    )
    assert model_id in ["gemini-1.5-pro", "gpt-4o", "claude-3-5-sonnet-latest"]
    assert confidence > 0.6

    model_id_cheap, _, _ = router.select_model(
        task_type="translation",
        prompt_size=500,
        budget_remaining=0.01
    )
    assert model_id_cheap == "llama3"

def test_platform_generates_and_broadcasts(ai_setup):
    platform = ai_setup["platform"]
    bus = ai_setup["event_bus"]

    events = []
    bus.subscribe("AIRequestStarted", lambda ev: events.append(ev))
    bus.subscribe("AIRequestCompleted", lambda ev: events.append(ev))

    response = platform.generate("Test query", task_type="advisory")
    assert "Mock" in response
    assert len(events) == 2
    assert events[0].payload["model_id"] is not None
    assert events[1].payload["cost"] is not None

def test_platform_fallback_routing(ai_setup):
    platform = ai_setup["platform"]
    reg = ai_setup["registry"]
    bus = ai_setup["event_bus"]

    fallback_events = []
    bus.subscribe("AIFallbackTriggered", lambda ev: fallback_events.append(ev))

    class BrokenAdapter:
        def generate(self, *args, **kwargs):
            raise RuntimeError("Cloud service timeout")
        def generate_stream(self, *args, **kwargs):
            raise RuntimeError("Cloud service timeout")

    reg.register_adapter("gemini-1.5-pro", BrokenAdapter())

    response = platform.generate("Retrieve weather", task_type="reasoning")
    assert "Mock" in response
    assert len(fallback_events) >= 1
    assert fallback_events[0].payload["original_model_id"] == "gemini-1.5-pro"
