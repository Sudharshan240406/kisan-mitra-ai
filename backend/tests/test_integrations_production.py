import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.core.config import Settings, validate_production_config
from app.core.container import Container
from app.core.integrations.adapters.weather import (
    IMDWeatherAdapter,
    OpenWeatherAdapter,
    TomorrowIOWeatherAdapter,
)
from app.core.integrations.adapters.market import (
    AgmarknetMarketAdapter,
    eNAMMarketAdapter,
)
from app.core.integrations.adapters.storage import CloudStorageAdapter
from app.core.integrations.adapters.authentication import LocalAuthAdapter, OAuthAdapter
from app.core.integrations.resilience import ResilientRunner


@pytest.mark.asyncio
async def test_weather_adapters_fallback_on_network_failure():
    """Checks that weather adapters fall back to mock data on HTTP errors."""
    imd = IMDWeatherAdapter()
    openweather = OpenWeatherAdapter()
    tomorrow = TomorrowIOWeatherAdapter()

    # IMD
    with patch("httpx.AsyncClient.get", side_effect=httpx.RequestError("Network Offline")):
        res = await imd.get_forecast("Delhi")
        assert res["provider"] == "IMD"
        assert res["temperature_c"] == 31.5

    # OpenWeather (without API key, should fallback)
    res = await openweather.get_forecast("Mumbai")
    assert res["provider"] == "OpenWeather"
    assert res["temperature_c"] == 29.8

    # Tomorrow.io
    res = await tomorrow.get_forecast("Bangalore")
    assert res["provider"] == "Tomorrow.io"
    assert res["temperature_c"] == 28.5


@pytest.mark.asyncio
async def test_market_price_adapters_normalization():
    """Checks that market prices are normalized correctly."""
    agmark = AgmarknetMarketAdapter()
    enam = eNAMMarketAdapter()

    # Check fallbacks
    res_ag = await agmark.get_market_price("Wheat", "Punjab")
    assert res_ag["provider"] == "Agmarknet"
    assert res_ag["modal_price_per_quintal"] == 2350

    res_en = await enam.get_market_price("Wheat", "Punjab")
    assert res_en["provider"] == "eNAM"
    assert res_en["modal_price_per_quintal"] == 2300


@pytest.mark.asyncio
async def test_cloud_storage_adapter_boto3_fallback():
    """Checks that CloudStorageAdapter falls back when boto3 credentials are missing."""
    storage = CloudStorageAdapter()
    assert await storage.health_check() is False

    await storage.write("test_key", "cloud_value")
    val = await storage.read("test_key")
    assert val == "cloud_value"


@pytest.mark.asyncio
async def test_authentication_jwt_and_oauth():
    """Checks authentication adapter token validation runs successfully."""
    local_auth = LocalAuthAdapter()
    oauth = OAuthAdapter()

    # Local Auth fallback check
    assert await local_auth.authenticate("admin", "valid-session-jwt-token") is True
    assert await local_auth.authenticate("guest", "invalid") is False

    # OAuth check
    assert await oauth.authenticate("admin", "oauth-token:secretvaluehere") is True
    assert await oauth.authenticate("user123", "invalid-oauth-token") is False


@pytest.mark.asyncio
async def test_telemetry_captures_integration_cost():
    """Verifies that ResilientRunner execute records integration latency and costs in telemetry."""
    container = Container()
    telemetry = container.telemetry

    runner = ResilientRunner(telemetry=telemetry)
    
    # Test simple mock call
    async def sample_op():
        return "success_val"

    result = await runner.execute(
        integration_id="stt-whisper",
        operation_name="transcribe",
        func=sample_op
    )
    assert result == "success_val"

    # Export metrics and verify
    metrics = telemetry.export_metrics()
    integration_metrics = metrics.get("integration_metrics", {})
    assert integration_metrics["total_calls"] >= 1
    assert integration_metrics["total_cost_usd"] > 0.0
    assert "stt-whisper" in integration_metrics["adapters"]


def test_production_config_validation():
    """Checks that validate_production_config flags missing credentials in production environment."""
    invalid_settings = Settings(
        APP_ENV="production",
        DB_PASSWORD="postgres",  # Security violation
        DB_USER="postgres",
        DEFAULT_LLM_PROVIDER="gemini",
        GEMINI_API_KEY=""  # Security violation
    )

    with pytest.raises(ValueError) as excinfo:
        validate_production_config(invalid_settings)

    assert "PRODUCTION SECURITY VIOLATION" in str(excinfo.value)
    assert "DB_PASSWORD" in str(excinfo.value)
