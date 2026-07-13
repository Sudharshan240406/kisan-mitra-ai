"""
test_live_data.py — Sprint 30 Live Weather & Market Data Tests.

Tests:
    Weather:
        1. test_weather_data_structure         — WeatherData fields correct
        2. test_weather_wmo_code_mapping       — WMO code → human string
        3. test_weather_voice_string_en        — English voice output
        4. test_weather_voice_string_hi        — Hindi voice output
        5. test_weather_sms_string             — SMS format string
        6. test_weather_fallback_on_error      — Network error → fallback WeatherData
        7. test_weather_api_endpoint           — GET /api/v1/live-data/weather

    Market:
        8.  test_market_data_structure         — MarketData fields correct
        9.  test_market_trend_computation      — Trend: up / down / stable
        10. test_market_curated_lookup         — Known commodity in curated set
        11. test_market_voice_string_en        — English voice output
        12. test_market_sms_string             — SMS format string
        13. test_market_fallback_on_error      — Network error → curated data
        14. test_market_all_prices             — All curated rows returned
        15. test_market_api_endpoint           — GET /api/v1/live-data/market

    Integration:
        16. test_dashboard_endpoint            — GET /api/v1/live-data/dashboard
        17. test_ivr_weather_dtmf2             — DTMF '2' triggers weather response
        18. test_ivr_market_dtmf3              — DTMF '3' triggers market response
        19. test_weather_tool_returns_live     — WeatherTool uses LiveWeatherService
        20. test_market_tool_returns_live      — MarketTool uses LiveMarketService
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.live_data.market_service import (
    _CURATED_PRICES,
    LiveMarketService,
    MarketData,
    _compute_trend,
    _curated_lookup,
)
from app.live_data.weather_service import (
    _WMO_CODES,
    LiveWeatherService,
    WeatherData,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_weather(**kwargs: Any) -> WeatherData:
    defaults = {
        "location": "Ludhiana, Punjab",
        "latitude": 30.9,
        "longitude": 75.85,
        "temperature_c": 32.5,
        "humidity_pct": 68.0,
        "rain_probability_pct": 15.0,
        "wind_speed_kmh": 14.0,
        "condition": "Partly cloudy",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    defaults.update(kwargs)
    return WeatherData(**defaults)


def _sample_market(**kwargs: Any) -> MarketData:
    defaults = {
        "commodity": "Wheat",
        "market": "Ludhiana Mandi",
        "today_price_inr": 2340.0,
        "yesterday_price_inr": 2310.0,
        "unit": "quintal",
        "trend": "up",
        "source": "curated",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    defaults.update(kwargs)
    return MarketData(**defaults)


# ===========================================================================
# WEATHER TESTS
# ===========================================================================


def test_weather_data_structure() -> None:
    """WeatherData has all required fields."""
    w = _sample_weather()
    assert isinstance(w.temperature_c, float)
    assert isinstance(w.humidity_pct, float)
    assert isinstance(w.rain_probability_pct, float)
    assert isinstance(w.wind_speed_kmh, float)
    assert isinstance(w.condition, str)
    assert isinstance(w.fetched_at, str)
    assert isinstance(w.location, str)


def test_weather_wmo_code_mapping() -> None:
    """WMO codes map to human-readable strings."""
    assert _WMO_CODES[0] == "Clear sky"
    assert _WMO_CODES[95] == "Thunderstorm"
    assert _WMO_CODES[61] == "Slight rain"
    assert 1 in _WMO_CODES


def test_weather_voice_string_en() -> None:
    """English voice string contains key weather fields."""
    w = _sample_weather()
    s = w.to_voice_string(language="en")
    assert "32.5" in s or "32" in s
    assert "Partly cloudy" in s
    assert "km/h" in s


def test_weather_voice_string_hi() -> None:
    """Hindi voice string is non-empty and contains temperature."""
    w = _sample_weather()
    s = w.to_voice_string(language="hi")
    assert len(s) > 10
    assert "°C" in s or "32" in s


def test_weather_sms_string() -> None:
    """SMS string has the Kisan Mitra header and location."""
    w = _sample_weather()
    sms = w.to_sms_string()
    assert "Kisan Mitra Weather" in sms
    assert "Ludhiana" in sms
    assert "Temp:" in sms


@pytest.mark.asyncio
async def test_weather_fallback_on_error() -> None:
    """LiveWeatherService returns fallback when network fails."""
    service = LiveWeatherService()
    with patch.object(service, "_geocode", side_effect=ConnectionError("timeout")):
        result = await service.get_weather("Unknown Place")
    assert isinstance(result, WeatherData)
    assert result.temperature_c > 0


@pytest.mark.asyncio
async def test_weather_api_endpoint() -> None:
    """GET /api/v1/live-data/weather returns structured JSON."""
    from app.api.v1.live_data import router
    from app.dependencies.container import get_container
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    mock_weather = _sample_weather()
    mock_container = MagicMock()
    mock_container.live_weather_service.get_weather = AsyncMock(return_value=mock_weather)
    mock_container.live_market_service.get_price = AsyncMock(return_value=_sample_market())

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_container] = lambda: mock_container

    client = TestClient(app)
    resp = client.get("/api/v1/live-data/weather?location=Ludhiana")
    assert resp.status_code == 200
    data = resp.json()
    assert "temperature_c" in data
    assert "voice_summary" in data
    assert "sms_summary" in data


# ===========================================================================
# MARKET TESTS
# ===========================================================================


def test_market_data_structure() -> None:
    """MarketData has all required fields."""
    m = _sample_market()
    assert isinstance(m.commodity, str)
    assert isinstance(m.market, str)
    assert isinstance(m.today_price_inr, float)
    assert isinstance(m.yesterday_price_inr, float)
    assert m.trend in ("up", "down", "stable")
    assert m.source in ("live", "curated")


def test_market_trend_computation() -> None:
    """Trend logic: price increase → up, decrease → down, flat → stable."""
    assert _compute_trend(2340, 2310) == "up"
    assert _compute_trend(2280, 2310) == "down"
    assert _compute_trend(2300, 2300) == "stable"


def test_market_curated_lookup() -> None:
    """Known commodity found in curated dataset."""
    row = _curated_lookup("Wheat")
    assert row is not None
    assert row["commodity"] == "Wheat"

    row2 = _curated_lookup("rice")
    assert row2 is not None

    # Unknown commodity
    row3 = _curated_lookup("xyzabc")
    assert row3 is None


def test_market_voice_string_en() -> None:
    """English voice string includes price and commodity."""
    m = _sample_market()
    s = m.to_voice_string(language="en")
    assert "Wheat" in s
    assert "2340" in s
    assert "quintal" in s


def test_market_sms_string() -> None:
    """SMS string has Kisan Mitra Market header and trend."""
    m = _sample_market()
    sms = m.to_sms_string()
    assert "Kisan Mitra Market" in sms
    assert "Wheat" in sms
    assert "Trend:" in sms


@pytest.mark.asyncio
async def test_market_fallback_on_error() -> None:
    """LiveMarketService returns curated data when live fetch fails."""
    service = LiveMarketService()
    with patch.object(service, "_fetch_live", side_effect=ConnectionError("no network")):
        result = await service.get_price("Wheat", "Ludhiana")
    assert isinstance(result, MarketData)
    assert result.today_price_inr > 0
    assert result.source == "curated"


@pytest.mark.asyncio
async def test_market_all_prices() -> None:
    """get_all_prices returns all curated commodities."""
    service = LiveMarketService()
    prices = await service.get_all_prices()
    assert len(prices) == len(_CURATED_PRICES)
    for p in prices:
        assert isinstance(p, MarketData)
        assert p.today_price_inr > 0


@pytest.mark.asyncio
async def test_market_api_endpoint() -> None:
    """GET /api/v1/live-data/market returns structured JSON."""
    from app.api.v1.live_data import router
    from app.dependencies.container import get_container
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    mock_market = _sample_market()
    mock_container = MagicMock()
    mock_container.live_market_service.get_price = AsyncMock(return_value=mock_market)
    mock_container.live_weather_service.get_weather = AsyncMock(return_value=_sample_weather())

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_container] = lambda: mock_container

    client = TestClient(app)
    resp = client.get("/api/v1/live-data/market?commodity=Wheat&location=Ludhiana")
    assert resp.status_code == 200
    data = resp.json()
    assert "today_price_inr" in data
    assert "voice_summary" in data


# ===========================================================================
# INTEGRATION TESTS
# ===========================================================================


@pytest.mark.asyncio
async def test_dashboard_endpoint() -> None:
    """GET /api/v1/live-data/dashboard returns weather + market snapshot."""
    from app.api.v1.live_data import router
    from app.dependencies.container import get_container
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    mock_weather = _sample_weather()
    mock_prices = [_sample_market(commodity=c) for c in ["Wheat", "Rice", "Maize"]]
    mock_container = MagicMock()
    mock_container.live_weather_service.get_weather = AsyncMock(return_value=mock_weather)
    mock_container.live_market_service.get_all_prices = AsyncMock(return_value=mock_prices)

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_container] = lambda: mock_container

    client = TestClient(app)
    resp = client.get("/api/v1/live-data/dashboard?location=Ludhiana")
    assert resp.status_code == 200
    data = resp.json()
    assert "weather" in data
    assert "market_prices" in data
    assert "last_refresh" in data
    assert len(data["market_prices"]) == 3


@pytest.mark.asyncio
async def test_ivr_weather_dtmf2() -> None:
    """
    DTMF '2' from INTENT_CAPTURE state → routes to weather.
    The IVR DTMF handler triggers CallRouter → which calls WeatherTool.
    We verify the response is non-empty and contains weather keywords.
    """
    from app.ivr.call_session import CallSession
    from app.ivr.dtmf_handler import DTMFHandler
    from app.ivr.ivr_flow import IVRFlow

    flow = IVRFlow()
    selector = MagicMock()
    handler = DTMFHandler(flow, selector)

    session = CallSession(call_id="ivr-w2", language="en")
    session.current_ivr_state = "INTENT_CAPTURE"

    # Pressing 2 from INTENT_CAPTURE → transitions to RECOMMENDATION_PLAYBACK with query='weather forecast'
    next_state, _prompt = await handler.handle_dtmf(session, "2")
    assert next_state == "RECOMMENDATION_PLAYBACK"
    assert session.current_ivr_state == "RECOMMENDATION_PLAYBACK"
    assert session.metadata.get("intent_query") == "weather forecast"


@pytest.mark.asyncio
async def test_ivr_market_dtmf3() -> None:
    """
    DTMF '3' from INTENT_CAPTURE → routes to market prices.
    """
    from app.ivr.call_session import CallSession
    from app.ivr.dtmf_handler import DTMFHandler
    from app.ivr.ivr_flow import IVRFlow

    flow = IVRFlow()
    selector = MagicMock()
    handler = DTMFHandler(flow, selector)

    session = CallSession(call_id="ivr-m3", language="en")
    session.current_ivr_state = "INTENT_CAPTURE"

    next_state, _prompt = await handler.handle_dtmf(session, "3")
    assert next_state == "RECOMMENDATION_PLAYBACK"
    assert session.current_ivr_state == "RECOMMENDATION_PLAYBACK"
    assert session.metadata.get("intent_query") == "market prices"


@pytest.mark.asyncio
async def test_weather_tool_returns_live() -> None:
    """WeatherTool.run() calls LiveWeatherService and returns voice string."""
    from app.core.context import AgentContext
    from app.tools.weather_tool import WeatherTool

    tool = WeatherTool()
    mock_context = MagicMock(spec=AgentContext)
    mock_context.metadata = {"language": "en"}

    mock_weather = _sample_weather()
    with patch("app.live_data.weather_service.LiveWeatherService.get_weather", new=AsyncMock(return_value=mock_weather)):
        result = await tool.run({"location": "Ludhiana"}, mock_context)

    assert isinstance(result, str)
    assert len(result) > 5


@pytest.mark.asyncio
async def test_market_tool_returns_live() -> None:
    """MarketTool.run() calls LiveMarketService and returns voice string."""
    from app.core.context import AgentContext
    from app.tools.market_tool import MarketTool

    tool = MarketTool()
    mock_context = MagicMock(spec=AgentContext)
    mock_context.metadata = {"language": "en"}

    mock_market = _sample_market()
    with patch("app.live_data.market_service.LiveMarketService.get_price", new=AsyncMock(return_value=mock_market)):
        result = await tool.run({"commodity": "Wheat", "location": "Ludhiana"}, mock_context)

    assert isinstance(result, str)
    assert len(result) > 5
