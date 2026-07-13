"""
market_tool.py — Routes market price queries through LiveMarketService.

The AI Orchestrator calls this tool when a farmer asks about mandi prices.
Uses LiveMarketService (Agmarknet live → curated fallback).
"""
import logging
from typing import Any

from app.core.context import AgentContext
from app.core.tool import BaseTool

logger = logging.getLogger("kisan_mitra_ai.tools.market_tool")


class MarketTool(BaseTool):
    """
    MarketTool: fetches live mandi prices, returns voice-ready text.
    """
    def __init__(self) -> None:
        super().__init__(
            name="MarketTool",
            description="Fetches live mandi crop prices from Agmarknet / curated fallback."
        )

    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        commodity = args.get("commodity", "Wheat")
        location = args.get("location", "")
        language = "en"
        if context and context.metadata:
            language = context.metadata.get("language", "en")

        try:
            from app.live_data.market_service import LiveMarketService
            service = LiveMarketService()
            price = await service.get_price(commodity, location)
            logger.info(f"[MarketTool] Price fetched for '{commodity}': ₹{price.today_price_inr}/quintal ({price.source})")
            return price.to_voice_string(language=language)
        except Exception as exc:
            logger.warning(f"[MarketTool] Live fetch failed: {exc}. Returning static fallback.")
            return f"MarketTool: Price of {commodity} is approximately ₹2,200 per quintal."
