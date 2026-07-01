import logging
import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.knowledge import KnowledgeProvider

logger = logging.getLogger("kisan_mitra_ai.knowledge.modules.market")


class MarketKnowledgeProvider(KnowledgeProvider):
    """
    Catalog of crop market commodities, mandi transaction logs, and supply-demand trends.
    """
    def __init__(self) -> None:
        self.market_trends: list[dict[str, Any]] = [
            {
                "id": "wheat_delhi",
                "commodity": "Wheat",
                "mandi": "Delhi Narela Mandi",
                "modal_price": 2450.0,
                "price_trend": "upward",
                "demand": "high",
                "supply": "moderate",
                "notes": "Prices are expected to rise by 5% due to reduced local arrivals.",
                "tags": ["wheat", "delhi", "narela", "cereal"]
            },
            {
                "id": "rice_bengaluru",
                "commodity": "Rice (Basmati)",
                "mandi": "Bengaluru Yeshwanthpur Mandi",
                "modal_price": 5400.0,
                "price_trend": "stable",
                "demand": "steady",
                "supply": "stable",
                "notes": "Standard Basmati variety is trading steadily. No major fluctuations.",
                "tags": ["rice", "basmati", "bengaluru", "grain"]
            },
            {
                "id": "potato_agra",
                "commodity": "Potato",
                "mandi": "Agra Mandi",
                "modal_price": 1200.0,
                "price_trend": "downward",
                "demand": "moderate",
                "supply": "high",
                "notes": "Potato supply surplus has triggered price corrections across Western UP mandis.",
                "tags": ["potato", "vegetable", "agra", "surplus"]
            }
        ]

    async def search(
        self,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Market pricing search: '{query}'")
        query_lower = query.lower()
        results = []
        for trend in self.market_trends:
            score = 0.0
            if query_lower in trend["commodity"].lower():
                score += 0.8
            if query_lower in trend["mandi"].lower():
                score += 0.5
            if query_lower in trend["notes"].lower():
                score += 0.3
            if any(query_lower in tag for tag in trend["tags"]):
                score += 0.4

            if score > 0.0:
                results.append({
                    "id": trend["id"],
                    "title": f"Market report for {trend['commodity']} at {trend['mandi']}",
                    "content": f"Trading modal price is INR {trend['modal_price']} per quintal. Trend: {trend['price_trend']}. Demand: {trend['demand']}. Supply: {trend['supply']}. {trend['notes']}",
                    "metadata": {
                        "commodity": trend["commodity"],
                        "mandi": trend["mandi"],
                        "modal_price": trend["modal_price"],
                        "price_trend": trend["price_trend"],
                        "last_updated": time.time()
                    },
                    "score": round(min(score, 1.0), 2),
                    "source": "market_prices_db"
                })

        results.sort(key=lambda x: float(x["score"]), reverse=True)
        return results[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {
            "provider": "MarketKnowledge",
            "status": "healthy",
            "market_trends_count": len(self.market_trends)
        }
