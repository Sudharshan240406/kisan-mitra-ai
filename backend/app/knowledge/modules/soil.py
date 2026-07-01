import logging
import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.knowledge import KnowledgeProvider

logger = logging.getLogger("kisan_mitra_ai.knowledge.modules.soil")


class SoilKnowledgeProvider(KnowledgeProvider):
    """
    Catalog of soil types, NPK indexes, organic carbon, pH ratings, and corrections.
    """
    def __init__(self) -> None:
        self.soils: list[dict[str, Any]] = [
            {
                "id": "alluvial",
                "name": "Alluvial Soil",
                "description": "Rich in potash but highly deficient in Nitrogen and Phosphorus. Found in Indo-Gangetic plains.",
                "typical_npk": "Low Nitrogen, Moderate Phosphorus, High Potash",
                "ph_range": [6.5, 7.8],
                "organic_carbon": "Low to Medium (0.3% - 0.5%)",
                "fertilization_recs": "Supplement with chemical nitrogen (Urea) and rock phosphate. Apply organic compost.",
                "tags": ["alluvial", "plains", "clayey", "sandy loam", "potash"]
            },
            {
                "id": "black",
                "name": "Black Soil (Regur)",
                "description": "High water-retention capacity. Rich in calcium, carbonate, potash, and lime. Poor in phosphorus.",
                "typical_npk": "Moderate Nitrogen, Low Phosphorus, Moderate Potash",
                "ph_range": [7.3, 8.5],
                "organic_carbon": "Medium (0.5% - 0.7%)",
                "fertilization_recs": "Avoid excessive watering. Add phosphorus-rich compounds. Gypsum application counters sodicity.",
                "tags": ["black", "regur", "clay", "cotton soil", "moisture retention"]
            },
            {
                "id": "red",
                "name": "Red Soil",
                "description": "Formed by weathering of crystalline rocks. Deficient in nitrogen, phosphorus, humus, and lime.",
                "typical_npk": "Low Nitrogen, Low Phosphorus, Moderate Potash",
                "ph_range": [5.5, 6.5],
                "organic_carbon": "Low (0.2% - 0.4%)",
                "fertilization_recs": "Acidic nature. Apply agricultural lime (calcium carbonate) to increase pH. Use organic farm yard manure (FYM).",
                "tags": ["red", "acidic", "iron", "sandy", "leaching"]
            }
        ]

    async def search(
        self,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Soil knowledge search: '{query}'")
        query_lower = query.lower()
        results = []
        for soil in self.soils:
            score = 0.0
            if query_lower in soil["name"].lower():
                score += 0.8
            if query_lower in soil["description"].lower():
                score += 0.4
            if query_lower in soil["fertilization_recs"].lower():
                score += 0.3
            if any(query_lower in tag for tag in soil["tags"]):
                score += 0.5

            if score > 0.0:
                results.append({
                    "id": soil["id"],
                    "title": f"Soil chemical report for {soil['name']}",
                    "content": f"{soil['description']} Typical NPK: {soil['typical_npk']}. Optimal pH: {soil['ph_range'][0]}-{soil['ph_range'][1]}. Carbon: {soil['organic_carbon']}. Recommendations: {soil['fertilization_recs']}.",
                    "metadata": {
                        "ph_range": soil["ph_range"],
                        "organic_carbon": soil["organic_carbon"],
                        "last_updated": time.time()
                    },
                    "score": round(min(score, 1.0), 2),
                    "source": "soil_chemistry_manuals"
                })

        results.sort(key=lambda x: float(x["score"]), reverse=True)
        return results[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {
            "provider": "SoilKnowledge",
            "status": "healthy",
            "soils_count": len(self.soils)
        }
