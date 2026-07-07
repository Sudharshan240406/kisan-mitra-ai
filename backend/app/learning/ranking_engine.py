import logging
from typing import Any, Dict, List, Optional

from app.learning.recommendation_optimizer import RecommendationOptimizer

logger = logging.getLogger("kisan_mitra_ai.learning.ranking_engine")

class RankingEngine:
    """
    Reranks and sorts candidate recommendations based on learned preference weights and farmer context.
    """
    def __init__(self, optimizer: Optional[RecommendationOptimizer] = None) -> None:
        self.optimizer = optimizer or RecommendationOptimizer()

    def rank_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Applies learned preference score boosts to candidates and sorts them in descending order.
        """
        ranked_list = []
        for rec in recommendations:
            rec_copy = rec.copy()
            base_score = rec_copy.get("score") or rec_copy.get("confidence") or 0.5

            # Retrieve optimizer preference boost
            boost = self.optimizer.score_recommendation(rec_copy, context)

            # Combine baseline score and feedback preference boost
            composite = base_score + boost
            final_score = float(max(0.0, min(1.0, composite)))

            rec_copy["score"] = round(final_score, 4)
            # Maintain confidence value
            if "confidence" in rec_copy:
                rec_copy["confidence"] = round(final_score, 4)

            rec_copy["preference_boost"] = round(boost, 4)
            ranked_list.append(rec_copy)

        # Sort descending by score
        ranked_list.sort(key=lambda x: x["score"], reverse=True)
        return ranked_list
