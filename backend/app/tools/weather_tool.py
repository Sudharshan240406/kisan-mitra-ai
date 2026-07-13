"""
weather_tool.py — Routes weather queries through LiveWeatherService.

The AI Orchestrator calls this tool when a farmer asks about weather.
It uses LiveWeatherService (Open-Meteo, no API key) and falls back
to the static string if the live fetch fails.
"""
import logging
from typing import Any

from app.core.context import AgentContext
from app.core.tool import BaseTool

logger = logging.getLogger("kisan_mitra_ai.tools.weather_tool")


class WeatherTool(BaseTool):
    """
    WeatherTool: fetches live weather via Open-Meteo, returns voice-ready text.
    """
    def __init__(self) -> None:
        super().__init__(
            name="WeatherTool",
            description="Fetches live weather forecast from Open-Meteo for any location."
        )

    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        location = args.get("location", "India")
        language = "hi"
        if context and context.metadata:
            language = context.metadata.get("language", "en")

        try:
            from app.live_data.weather_service import LiveWeatherService
            service = LiveWeatherService()
            weather = await service.get_weather(location)
            logger.info(f"[WeatherTool] Live weather fetched for '{location}': {weather.condition}")
            return weather.to_voice_string(language=language)
        except Exception as exc:
            logger.warning(f"[WeatherTool] Live fetch failed: {exc}. Returning static fallback.")
            return f"WeatherTool: Forecast for {location} is approximately 30°C with moderate humidity."
