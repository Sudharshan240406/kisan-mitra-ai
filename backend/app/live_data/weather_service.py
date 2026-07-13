"""
weather_service.py — Live weather data via Open-Meteo (no API key required).

Open-Meteo API: https://open-meteo.com/en/docs
Geocoding API:  https://geocoding-api.open-meteo.com/v1/search

Flow:
  1. Geocode the location string → lat/lon
  2. Fetch current weather from Open-Meteo
  3. Return a WeatherData dataclass + a human-readable voice string
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

logger = logging.getLogger("kisan_mitra_ai.live_data.weather")

_GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# WMO Weather interpretation codes → human readable
_WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Heavy drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Heavy rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


@dataclass
class WeatherData:
    """Structured weather result returned by LiveWeatherService."""
    location: str
    latitude: float
    longitude: float
    temperature_c: float
    humidity_pct: float
    rain_probability_pct: float
    wind_speed_kmh: float
    condition: str
    fetched_at: str  # ISO-8601 UTC

    def to_voice_string(self, language: str = "en") -> str:
        """Return a short TTS-ready sentence."""
        if language == "hi":
            return (
                f"{self.location} में अभी मौसम: {self.condition}। "
                f"तापमान {self.temperature_c:.1f}°C, आर्द्रता {self.humidity_pct:.0f}%, "
                f"हवा {self.wind_speed_kmh:.0f} किमी/घंटा, बारिश की संभावना {self.rain_probability_pct:.0f}%।"
            )
        return (
            f"Current weather in {self.location}: {self.condition}. "
            f"Temperature {self.temperature_c:.1f}°C, humidity {self.humidity_pct:.0f}%, "
            f"wind {self.wind_speed_kmh:.0f} km/h, rain probability {self.rain_probability_pct:.0f}%."
        )

    def to_sms_string(self) -> str:
        return (
            f"🌤 Kisan Mitra Weather — {self.location}\n"
            f"Condition: {self.condition}\n"
            f"Temp: {self.temperature_c:.1f}°C | Humidity: {self.humidity_pct:.0f}%\n"
            f"Wind: {self.wind_speed_kmh:.0f} km/h | Rain: {self.rain_probability_pct:.0f}%\n"
            f"Updated: {self.fetched_at[:16]} UTC"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "temperature_c": self.temperature_c,
            "humidity_pct": self.humidity_pct,
            "rain_probability_pct": self.rain_probability_pct,
            "wind_speed_kmh": self.wind_speed_kmh,
            "condition": self.condition,
            "fetched_at": self.fetched_at,
        }


# Default location used when geocoding fails or location is unknown
_FALLBACK_WEATHER = WeatherData(
    location="India (fallback)",
    latitude=20.5937,
    longitude=78.9629,
    temperature_c=30.0,
    humidity_pct=65.0,
    rain_probability_pct=20.0,
    wind_speed_kmh=12.0,
    condition="Partly cloudy",
    fetched_at=datetime.now(timezone.utc).isoformat(),
)


class LiveWeatherService:
    """
    Fetches live weather data from Open-Meteo for any Indian location.
    No API key required.
    """

    TIMEOUT = 6.0  # seconds

    async def get_weather(self, location: str) -> WeatherData:
        """
        Fetch live weather for the given location string.
        Falls back to _FALLBACK_WEATHER on any network/parse error.
        """
        try:
            lat, lon, resolved = await self._geocode(location)
        except Exception as exc:
            logger.warning(f"[LiveWeather] Geocoding failed for '{location}': {exc}. Using fallback.")
            return _FALLBACK_WEATHER

        try:
            return await self._fetch_weather(lat, lon, resolved)
        except Exception as exc:
            logger.warning(f"[LiveWeather] Weather fetch failed for ({lat},{lon}): {exc}. Using fallback.")
            return WeatherData(
                location=resolved,
                latitude=lat,
                longitude=lon,
                temperature_c=_FALLBACK_WEATHER.temperature_c,
                humidity_pct=_FALLBACK_WEATHER.humidity_pct,
                rain_probability_pct=_FALLBACK_WEATHER.rain_probability_pct,
                wind_speed_kmh=_FALLBACK_WEATHER.wind_speed_kmh,
                condition=_FALLBACK_WEATHER.condition,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

    async def _geocode(self, location: str) -> tuple[float, float, str]:
        """Resolve a location string to lat/lon using Open-Meteo Geocoding."""
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            resp = await client.get(
                _GEO_URL,
                params={"name": location, "count": 1, "language": "en", "format": "json"},
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            if not results:
                raise ValueError(f"No geocoding results for '{location}'")
            r = results[0]
            name = r.get("name", location)
            state = r.get("admin1", "")
            resolved = f"{name}, {state}".strip(", ")
            return float(r["latitude"]), float(r["longitude"]), resolved

    async def _fetch_weather(self, lat: float, lon: float, location: str) -> WeatherData:
        """Fetch current weather from Open-Meteo forecast endpoint."""
        params: dict[str, Any] = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation_probability",
                "wind_speed_10m",
                "weather_code",
            ],
            "timezone": "Asia/Kolkata",
        }
        async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
            resp = await client.get(_WEATHER_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        wmo_code = int(current.get("weather_code", 1))
        condition = _WMO_CODES.get(wmo_code, "Variable")

        return WeatherData(
            location=location,
            latitude=lat,
            longitude=lon,
            temperature_c=float(current.get("temperature_2m", 30.0)),
            humidity_pct=float(current.get("relative_humidity_2m", 60.0)),
            rain_probability_pct=float(current.get("precipitation_probability", 0.0)),
            wind_speed_kmh=float(current.get("wind_speed_10m", 10.0)),
            condition=condition,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )
