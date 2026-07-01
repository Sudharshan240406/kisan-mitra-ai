import logging
import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.knowledge import KnowledgeProvider

logger = logging.getLogger("kisan_mitra_ai.knowledge.modules.disease")


class DiseaseKnowledgeProvider(KnowledgeProvider):
    """
    Catalog of crop diseases, visual symptoms, pathogen families, and chemical/organic treatments.
    """
    def __init__(self) -> None:
        self.diseases: list[dict[str, Any]] = [
            {
                "id": "wheat_rust",
                "name": "Wheat Rust (Puccinia)",
                "pathogen_type": "Fungal",
                "crop_targets": ["wheat"],
                "symptoms": ["yellow-orange pustules on leaves", "stripe markings on leaf blade", "brown dust powder on stems"],
                "prevention_measures": ["Use rust-resistant wheat seed varieties", "Avoid late sowing", "Clean weeds around boundaries"],
                "treatment_chemical": ["Propiconazole 25% EC (200 ml in 200 liters water)", "Tebuconazole"],
                "treatment_organic": ["Neem oil spray (5ml per liter)", "Pseudomonas fluorescens biological agent spray"],
                "severity": "critical",
                "tags": ["wheat", "rust", "yellow rust", "stripe rust", "fungus", "pustule"]
            },
            {
                "id": "rice_blast",
                "name": "Rice Blast (Magnaporthe oryzae)",
                "pathogen_type": "Fungal",
                "crop_targets": ["rice"],
                "symptoms": ["spindle-shaped lesions on leaves", "ashy-gray centers with brown borders", "neck rot at panicle nodes"],
                "prevention_measures": ["Avoid excessive nitrogen application", "Sow seed at recommended spacing", "Use certified seed"],
                "treatment_chemical": ["Tricyclazole 75% WP (120 g per acre)", "Isoprothiolane"],
                "treatment_organic": ["Trichoderma viride biological spray", "Fermented cow urine liquid spray"],
                "severity": "critical",
                "tags": ["rice", "paddy", "blast", "lesions", "fungus", "neck rot"]
            },
            {
                "id": "potato_late_blight",
                "name": "Potato Late Blight (Phytophthora)",
                "pathogen_type": "Fungal-like (Oomycete)",
                "crop_targets": ["potato"],
                "symptoms": ["water-soaked dark spots on leaves", "white fuzzy mold on leaf undersides in humid weather", "rotten brown tubers"],
                "prevention_measures": ["Plant disease-free seed tubers", "Ensure tall earthing up ridges", "Monitor weather forecast warnings"],
                "treatment_chemical": ["Mancozeb 75% WP", "Metalaxyl + Mancozeb combination spray"],
                "treatment_organic": ["Copper oxychloride spray", "Bordeaux mixture 1% spray"],
                "severity": "high",
                "tags": ["potato", "late blight", "blight", "mold", "rot", "spots"]
            }
        ]

    async def search(
        self,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Disease pathology search: '{query}'")
        query_lower = query.lower()
        results = []
        for disease in self.diseases:
            score = 0.0
            if query_lower in disease["name"].lower():
                score += 0.8
            if query_lower in disease["pathogen_type"].lower():
                score += 0.3
            if any(query_lower in sym.lower() for sym in disease["symptoms"]):
                score += 0.6
            if any(query_lower in tag for tag in disease["tags"]):
                score += 0.4

            # Crop context match boosting
            if context and context.crop:
                if context.crop.lower() in disease["crop_targets"]:
                    score += 0.2

            if score > 0.0:
                results.append({
                    "id": disease["id"],
                    "title": f"Pathology profile for {disease['name']}",
                    "content": f"Symptoms: {', '.join(disease['symptoms'])}. Prevention: {', '.join(disease['prevention_measures'])}. Chemical treatment: {', '.join(disease['treatment_chemical'])}. Organic treatment: {', '.join(disease['treatment_organic'])}.",
                    "metadata": {
                        "pathogen_type": disease["pathogen_type"],
                        "crop_targets": disease["crop_targets"],
                        "severity": disease["severity"],
                        "last_updated": time.time()
                    },
                    "score": round(min(score, 1.0), 2),
                    "source": "crop_pathology_manuals"
                })

        results.sort(key=lambda x: float(x["score"]), reverse=True)
        return results[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {
            "provider": "DiseaseKnowledge",
            "status": "healthy",
            "diseases_count": len(self.diseases)
        }
