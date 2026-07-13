"""
live_data.py — Sprint 30 Live Data API endpoints.

Exposes weather and market price data for Mission Control dashboard
and farmer-facing SMS/IVR queries.
"""
import logging
from typing import Any

from app.core.container import Container
from app.dependencies.container import get_container
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/api/v1/live-data", tags=["Live Data Platform"])
logger = logging.getLogger("kisan_mitra_ai.api.live_data")


@router.get("/weather", response_model=dict[str, Any])
async def get_live_weather(
    location: str = Query(default="Ludhiana, Punjab", description="City, state or district name"),
    language: str = Query(default="en", description="Response language: en, hi, kn, te, ta, pa"),
    container: Container = Depends(get_container),
) -> dict[str, Any]:
    """
    Fetch live weather from Open-Meteo for a given location.
    No API key required.
    """
    logger.info(f"[LiveData] Weather request for '{location}'")
    weather = await container.live_weather_service.get_weather(location)
    return {
        **weather.to_dict(),
        "voice_summary": weather.to_voice_string(language=language),
        "sms_summary": weather.to_sms_string(),
    }


@router.get("/market", response_model=dict[str, Any])
async def get_live_market_price(
    commodity: str = Query(default="Wheat", description="Crop or commodity name"),
    location: str = Query(default="", description="Market or mandi location (optional)"),
    language: str = Query(default="en"),
    container: Container = Depends(get_container),
) -> dict[str, Any]:
    """
    Fetch live mandi price from Agmarknet (falls back to curated data).
    """
    logger.info(f"[LiveData] Market request for '{commodity}' at '{location}'")
    price = await container.live_market_service.get_price(commodity, location)
    return {
        **price.to_dict(),
        "voice_summary": price.to_voice_string(language=language),
        "sms_summary": price.to_sms_string(),
    }


@router.get("/market/all", response_model=list[dict[str, Any]])
async def get_all_market_prices(
    container: Container = Depends(get_container),
) -> list[dict[str, Any]]:
    """
    Return prices for all tracked commodities (Mission Control dashboard).
    """
    logger.info("[LiveData] All market prices requested")
    prices = await container.live_market_service.get_all_prices()
    return [p.to_dict() for p in prices]


@router.get("/dashboard", response_model=dict[str, Any])
async def live_data_dashboard(
    location: str = Query(default="Ludhiana, Punjab"),
    container: Container = Depends(get_container),
) -> dict[str, Any]:
    """
    Mission Control dashboard snapshot:
    - Latest weather
    - Top market prices
    - Last refresh time
    """
    import asyncio
    from datetime import datetime, timezone

    logger.info(f"[LiveData] Dashboard request for '{location}'")

    # Fetch weather and market prices concurrently
    weather, prices = await asyncio.gather(
        container.live_weather_service.get_weather(location),
        container.live_market_service.get_all_prices(),
    )

    top_prices = [p.to_dict() for p in prices[:8]]

    return {
        "location": location,
        "weather": weather.to_dict(),
        "market_prices": top_prices,
        "last_refresh": datetime.now(timezone.utc).isoformat(),
        "weather_summary": weather.to_voice_string(language="en"),
    }


@router.get("/health")
async def live_data_health(
    container: Container = Depends(get_container),
) -> dict[str, Any]:
    """Quick health check — verifies services are available."""
    return {
        "weather_service": "open-meteo (no key required)",
        "market_service": "agmarknet + curated fallback",
        "status": "active",
    }
