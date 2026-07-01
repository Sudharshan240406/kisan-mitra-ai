import logging
import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.knowledge import KnowledgeProvider

logger = logging.getLogger("kisan_mitra_ai.knowledge.modules.weather")


class WeatherKnowledgeProvider(KnowledgeProvider):
    """
    Catalog of weather parameter advisories, extreme events, and seasonal warning profiles.
    """
    def __init__(self) -> None:
        self.advisories: list[dict[str, Any]] = [
            {
                "id": "monsoon_delayed",
                "condition": "delayed monsoon",
                "advisory": "Sow short-duration drought-resistant crop varieties such as Pearl Millet (Bajra) or Sorghum. Apply mulching to conserve soil moisture.",
                "severity": "high",
                "tags": ["monsoon", "delay", "rain", "drought", "dry"]
            },
            {
                "id": "excessive_rainfall",
                "condition": "heavy rain forecast",
                "advisory": "Ensure proper drainage channels in crop fields to prevent waterlogging. Postpone application of fertilizers and chemical sprays.",
                "severity": "medium",
                "tags": ["rain", "flood", "drainage", "storm", "monsoon"]
            },
            {
                "id": "frost_warning",
                "condition": "sudden temperature drop / frost",
                "advisory": "Irrigate crops lightly during the evening to maintain soil temperature. Burn agricultural waste around fields to create smoke cover.",
                "severity": "high",
                "tags": ["frost", "cold", "winter", "temperature", "freeze"]
            },
            {
                "id": "high_heat_index",
                "condition": "heatwave",
                "advisory": "Irrigate crops frequently early in the morning or late evening. Do not spray herbicides in dry wind conditions.",
                "severity": "medium",
                "tags": ["heat", "summer", "temperature", "evaporation", "dry"]
            }
        ]

    async def search(
        self,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Weather knowledge search: '{query}'")
        query_lower = query.lower()
        results = []
        for adv in self.advisories:
            score = 0.0
            if query_lower in adv["condition"].lower():
                score += 0.8
            if query_lower in adv["advisory"].lower():
                score += 0.3
            if any(query_lower in tag for tag in adv["tags"]):
                score += 0.5

            if score > 0.0:
                results.append({
                    "id": adv["id"],
                    "title": f"Weather Advisory for {adv['condition'].capitalize()}",
                    "content": adv["advisory"],
                    "metadata": {
                        "severity": adv["severity"],
                        "last_updated": time.time()
                    },
                    "score": round(min(score, 1.0), 2),
                    "source": "weather_advisories_db"
                })

        results.sort(key=lambda x: float(x["score"]), reverse=True)
        return results[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {
            "provider": "WeatherKnowledge",
            "status": "healthy",
            "advisories_count": len(self.advisories)
        }
