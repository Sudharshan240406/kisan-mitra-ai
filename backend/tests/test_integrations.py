import asyncio
import time
from typing import Any
import pytest
from fastapi.testclient import TestClient

from app.core.container import Container
from app.core.context import AgentContext
from app.core.event_bus import EventBus
from app.core.integrations.base import (
    IIntegration,
    IntegrationMetadata,
    IWeatherAdapter,
)
from app.core.integrations.registry import IntegrationRegistry
from app.core.integrations.resilience import (
    CircuitBreaker,
    CircuitBreakerOpenException,
    ResilientRunner,
)
from app.core.telemetry import TelemetryFramework
from app.main import app
from app.services.market_service import MarketService
from app.services.scheme_service import GovernmentSchemeService
from app.services.weather_service import WeatherService


# Mock implementation of an integration
class DummyWeatherAdapter(IWeatherAdapter):
    def __init__(self, provider_id: str = "dummy-weather", status: str = "active") -> None:
        self._metadata = IntegrationMetadata(
            id=provider_id,
            name="Dummy Weather Provider",
            version="1.0.0",
            description="Testing mock weather provider.",
            type="weather",
            status=status,
            capabilities=["forecast"],
            configuration={"endpoint": "http://dummy.io"},
            feature_flags={"enabled": True}
        )
        self.initialize_called = False
        self.cleanup_called = False
        self.health_check_result = True
        self.calls_count = 0

    @property
    def metadata(self) -> IntegrationMetadata:
        return self._metadata

    async def initialize(self) -> None:
        self.initialize_called = True

    async def cleanup(self) -> None:
        self.cleanup_called = True

    async def health_check(self) -> bool:
        return self.health_check_result

    async def get_forecast(self, location: str) -> dict[str, Any]:
        self.calls_count += 1
        if location == "raise_error":
            raise ConnectionError("Connection refused by dummy server")
        if location == "timeout":
            await asyncio.sleep(2.0)
        return {
            "provider": self.metadata.id,
            "location": location,
            "temperature_c": 25.0,
            "humidity_pct": 50,
            "warnings": ["Dummy Warn"]
        }


@pytest.mark.asyncio
async def test_integration_registry_lifecycle() -> None:
    event_bus = EventBus()
    registry = IntegrationRegistry(event_bus)
    adapter1 = DummyWeatherAdapter("dummy-1")
    adapter2 = DummyWeatherAdapter("dummy-2")

    # Registration
    registry.register(adapter1)
    registry.register(adapter2)

    assert registry.get("dummy-1") == adapter1
    assert registry.get("dummy-2") == adapter2
    assert registry.get_active("weather") == adapter1

    # Switch active provider
    registry.set_active("weather", "dummy-2")
    assert registry.get_active("weather") == adapter2

    # Duplicate ID check
    with pytest.raises(ValueError):
        registry.register(adapter1)

    # Deregistration
    registry.deregister("dummy-2")
    assert registry.get_active("weather") == adapter1
    assert len(registry.list_integrations()) == 1


@pytest.mark.asyncio
async def test_resilience_runner_success() -> None:
    event_bus = EventBus()
    telemetry = TelemetryFramework()
    runner = ResilientRunner(event_bus, telemetry)
    adapter = DummyWeatherAdapter()

    # Test successful execution
    res = await runner.execute(
        integration_id=adapter.metadata.id,
        operation_name="get_forecast",
        func=lambda: adapter.get_forecast("Amritsar")
    )
    assert res["location"] == "Amritsar"
    assert res["temperature_c"] == 25.0
    
    # Assert telemetry is recorded
    metrics = telemetry.export_metrics()
    assert "integration_metrics" in metrics
    assert metrics["integration_metrics"]["total_calls"] == 1
    assert metrics["integration_metrics"]["failure_count"] == 0


@pytest.mark.asyncio
async def test_resilience_runner_retries_and_circuit_breaker() -> None:
    event_bus = EventBus()
    telemetry = TelemetryFramework()
    # High failure rate breaker
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.5)
    runner = ResilientRunner(event_bus, telemetry, breaker)
    adapter = DummyWeatherAdapter()

    # Call with a function that throws ConnectionError (should trigger retries)
    with pytest.raises(ConnectionError):
        await runner.execute(
            integration_id=adapter.metadata.id,
            operation_name="get_forecast",
            func=lambda: adapter.get_forecast("raise_error"),
            retries=2,
            backoff_factor=1.0,
            timeout=1.0
        )

    # Confirm circuit breaker records failures (threshold was 2, we failed once with retries.
    # Actually, each failed attempt in the loop raises an exception. Let's see:
    # After retries run out, record_failure is called.
    assert breaker.failure_count == 1
    assert breaker.state == "CLOSED"

    # Trigger second final failure to open circuit
    with pytest.raises(ConnectionError):
        await runner.execute(
            integration_id=adapter.metadata.id,
            operation_name="get_forecast",
            func=lambda: adapter.get_forecast("raise_error"),
            retries=0,
            timeout=1.0
        )

    assert breaker.state == "OPEN"

    # Subsequent call should fail fast with CircuitBreakerOpenException
    with pytest.raises(CircuitBreakerOpenException):
        await runner.execute(
            integration_id=adapter.metadata.id,
            operation_name="get_forecast",
            func=lambda: adapter.get_forecast("Amritsar")
        )

    # Let breaker recover
    await asyncio.sleep(0.6)
    assert breaker.allow_execution() is True
    assert breaker.state == "HALF_OPEN"

    # Successful call should close breaker
    res = await runner.execute(
        integration_id=adapter.metadata.id,
        operation_name="get_forecast",
        func=lambda: adapter.get_forecast("Amritsar")
    )
    assert res["location"] == "Amritsar"
    assert breaker.state == "CLOSED"


@pytest.mark.asyncio
async def test_resilience_timeout_and_fallback() -> None:
    runner = ResilientRunner()
    adapter = DummyWeatherAdapter()

    # Test timeout logic
    with pytest.raises(asyncio.TimeoutError):
        await runner.execute(
            integration_id=adapter.metadata.id,
            operation_name="get_forecast",
            func=lambda: adapter.get_forecast("timeout"),
            retries=0,
            timeout=0.2
        )

    # Test fallback strategy
    fallback_data = {"fallback": "activated", "temperature_c": 20.0}
    res = await runner.execute(
        integration_id=adapter.metadata.id,
        operation_name="get_forecast",
        func=lambda: adapter.get_forecast("raise_error"),
        fallback=lambda: fallback_data,
        retries=0,
        timeout=1.0
    )
    assert res["fallback"] == "activated"
    assert res["temperature_c"] == 20.0


@pytest.mark.asyncio
async def test_service_bindings_routing() -> None:
    container = Container()
    # Clear auto registered weather adapters to control state
    container.integration_registry.deregister("imd-weather")
    container.integration_registry.deregister("openweather")

    # Add our dummy
    dummy = DummyWeatherAdapter("imd-weather")
    container.integration_registry.register(dummy)

    weather_service = WeatherService()
    context = AgentContext(
        request_id="req-1",
        trace_id="trace-1",
        session_id="ses-1",
        farmer_id=None,
        language="en"
    )
    context.metadata["container"] = container

    # Call service
    res_str = await weather_service.get_weather_forecast("Punjab", context)
    assert "Weather Integration (Dummy Weather Provider) output" in res_str
    assert "Forecast for Punjab is 25.0C" in res_str
    assert dummy.calls_count == 1


def test_api_router_endpoints() -> None:
    with TestClient(app) as client:
        # 1. List integrations
        res = client.get("/api/v1/integrations")
        assert res.status_code == 200
        data = res.json()
        assert len(data) > 0
        # Must contain imd-weather
        ids = [i["id"] for i in data]
        assert "imd-weather" in ids

        # 2. Toggle status
        res_toggle = client.post("/api/v1/integrations/openweather/toggle")
        assert res_toggle.status_code == 200
        assert res_toggle.json()["new_status"] in ["active", "inactive"]

        # 3. Activate provider
        res_act = client.post("/api/v1/integrations/openweather/activate")
        # OpenWeather can be activated if it's toggle status is active
        if res_toggle.json()["new_status"] == "active":
            assert res_act.status_code == 200
        else:
            # returns 400 because its status is inactive
            assert res_act.status_code == 400

        # Reset status if needed
        if res_toggle.json()["new_status"] == "inactive":
            client.post("/api/v1/integrations/openweather/toggle")

        # 4. Test run operation
        res_test = client.post("/api/v1/integrations/imd-weather/test")
        assert res_test.status_code == 200
        assert res_test.json()["status"] == "success"

        # 5. Metrics endpoint
        res_metrics = client.get("/api/v1/integrations/metrics")
        assert res_metrics.status_code == 200
        assert "adapters" in res_metrics.json()
        assert "imd-weather" in res_metrics.json()["adapters"]
