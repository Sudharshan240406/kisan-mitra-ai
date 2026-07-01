import logging
import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.knowledge import KnowledgeProvider

logger = logging.getLogger("kisan_mitra_ai.knowledge.modules.crop")


class CropKnowledgeProvider(KnowledgeProvider):
    """
    Catalog of crop lifecycle profiles, sowing guides, fertilizers, and harvesting steps.
    """
    def __init__(self) -> None:
        self.crops: list[dict[str, Any]] = [
            {
                "id": "wheat",
                "name": "Wheat",
                "lifecycle": "Sowing (Nov-Dec), Vegetative (Dec-Feb), Flowering (Feb-Mar), Harvesting (Mar-Apr).",
                "best_practices": "Sow seeds at 4-5 cm depth. Ensure proper seed rate of 100 kg per hectare.",
                "fertilizers": "Apply NPK in 120:60:40 ratio. Split Nitrogen in three doses.",
                "pesticides": "Use Chlorpyriphos to prevent termite damage during vegetative phase.",
                "season": "Rabi",
                "tags": ["wheat", "rabi", "grain", "cereal"]
            },
            {
                "id": "rice",
                "name": "Rice (Paddy)",
                "lifecycle": "Nursery Sowing (May-June), Transplanting (June-July), Tillering (Aug-Sept), Harvesting (Oct-Nov).",
                "best_practices": "Maintain standing water of 2-5 cm during transplanting. Keep spacing of 20x15 cm.",
                "fertilizers": "Apply NPK in 100:50:50 ratio. Zinc sulphate application (25 kg/ha) resolves zinc deficiency.",
                "pesticides": "Use Tricyclazole against blast disease.",
                "season": "Kharif",
                "tags": ["rice", "paddy", "kharif", "wetland"]
            },
            {
                "id": "potato",
                "name": "Potato",
                "lifecycle": "Planting (Oct-Nov), Earthing up (Nov-Dec), Tuber bulk (Dec-Jan), Harvesting (Feb-Mar).",
                "best_practices": "Plant tubers 10-12 cm deep. Earthing up should be done 30 days after planting.",
                "fertilizers": "Apply NPK in 150:100:120 ratio. High Potassium improves tuber sizing.",
                "pesticides": "Use Mancozeb to prevent Early and Late Blight disease outbreaks.",
                "season": "Rabi",
                "tags": ["potato", "tuber", "rabi", "vegetable"]
            }
        ]

    async def search(
        self,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Crop practices search: '{query}'")
        query_lower = query.lower()
        results = []
        for crop in self.crops:
            score = 0.0
            if query_lower in crop["name"].lower():
                score += 0.8
            if query_lower in crop["best_practices"].lower():
                score += 0.4
            if query_lower in crop["fertilizers"].lower():
                score += 0.3
            if any(query_lower in tag for tag in crop["tags"]):
                score += 0.5

            if score > 0.0:
                results.append({
                    "id": crop["id"],
                    "title": f"Agronomic cultivation manual for {crop['name']}",
                    "content": f"Lifecycle: {crop['lifecycle']}. Best practices: {crop['best_practices']}. Fertilization: {crop['fertilizers']}. Pesticides: {crop['pesticides']}.",
                    "metadata": {
                        "season": crop["season"],
                        "last_updated": time.time()
                    },
                    "score": round(min(score, 1.0), 2),
                    "source": "crop_agronomy_manuals"
                })

        results.sort(key=lambda x: float(x["score"]), reverse=True)
        return results[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {
            "provider": "CropKnowledge",
            "status": "healthy",
            "crops_count": len(self.crops)
        }
