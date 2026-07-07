import logging
from typing import Any, Dict, Optional

from app.learning.confidence_optimizer import ConfidenceOptimizer
from app.learning.feedback_engine import FeedbackEngine
from app.learning.feedback_store import FeedbackStore
from app.learning.ranking_engine import RankingEngine
from app.learning.recommendation_optimizer import RecommendationOptimizer

logger = logging.getLogger("kisan_mitra_ai.learning.learning_manager")

class LearningManager:
    """
    Central coordinator orchestrating feedback collection, confidence optimization,
    preference weights updates, and exposing learning analytics hooks.
    """
    def __init__(self, store: Optional[FeedbackStore] = None) -> None:
        self.store = store or FeedbackStore()
        self.feedback_engine = FeedbackEngine(store=self.store)
        self.confidence_optimizer = ConfidenceOptimizer()
        self.recommendation_optimizer = RecommendationOptimizer()
        self.ranking_engine = RankingEngine(optimizer=self.recommendation_optimizer)

        # Hydrate optimizers from disk history
        self._hydrate_optimizers()

    def _hydrate_optimizers(self) -> None:
        """
        Replays existing feedbacks on startup to build optimizer state.
        """
        for fb in self.store.recommendations:
            self.confidence_optimizer.update_offsets(fb)
            self.recommendation_optimizer.update_preferences(fb)

    def process_interaction(
        self,
        farmer_id: str,
        recommendation_id: str,
        context: Dict[str, Any],
        feedback_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processes an interaction outcome, triggers confidence and preference tuning,
        logs document utility, and persists results.
        """
        # Parse feedback flags
        accepted = bool(feedback_data.get("accepted", False))
        rejected = bool(feedback_data.get("rejected", False))
        ignored = bool(feedback_data.get("ignored", False))
        manual_correction = feedback_data.get("manual_correction")

        # Build metadata context
        metadata = {
            "crop": context.get("crop"),
            "region": context.get("region") or context.get("location"),
            "language": context.get("language") or "en",
            "scheme": context.get("scheme"),
            "advice_type": context.get("advice_type")
        }

        # 1. Log recommendation feedback
        fb = self.feedback_engine.record_recommendation_feedback(
            farmer_id=farmer_id,
            recommendation_id=recommendation_id,
            accepted=accepted,
            rejected=rejected,
            ignored=ignored,
            manual_correction=manual_correction,
            metadata=metadata
        )

        # 2. Update optimizers
        self.confidence_optimizer.update_offsets(fb)
        self.recommendation_optimizer.update_preferences(fb)

        # 3. Log cited / ignored document usage if provided in context
        cited_docs = context.get("cited_documents", [])
        for doc in cited_docs:
            action = "useful" if accepted else "cited"
            self.feedback_engine.record_knowledge_feedback(doc, action)

        ignored_docs = context.get("ignored_documents", [])
        for doc in ignored_docs:
            self.feedback_engine.record_knowledge_feedback(doc, "ignored")

        low_quality_docs = context.get("low_quality_documents", [])
        for doc in low_quality_docs:
            self.feedback_engine.record_knowledge_feedback(doc, "low_quality")

        # 4. Save to disk
        self.store.save_to_disk()

        return {
            "status": "success",
            "farmer_id": farmer_id,
            "recommendation_id": recommendation_id,
            "updated_confidence_offsets": {
                "crop": self.confidence_optimizer.crop_offsets.copy(),
                "region": self.confidence_optimizer.region_offsets.copy()
            }
        }

    def get_analytics(self) -> Dict[str, Any]:
        """
        Exposes internal metrics for Acceptance Rate, Recommendation Quality,
        Confidence Evolution, and Learning Progress.
        """
        recs = self.store.recommendations
        total_recs = len(recs)

        accepted_count = sum(1 for r in recs if r.accepted)
        rejected_count = sum(1 for r in recs if r.rejected)
        ignored_count = sum(1 for r in recs if r.ignored)

        # 1. Acceptance rate
        acceptance_rate = (accepted_count / total_recs) if total_recs > 0 else 0.0

        # 2. Recommendation quality (index out of 100 based on acceptance and rejections)
        quality_score = 0.0
        if total_recs > 0:
            quality_score = ((accepted_count * 1.0 + ignored_count * 0.3 - rejected_count * 0.5) / total_recs) * 100.0
            quality_score = max(0.0, min(100.0, quality_score))

        # 3. Confidence evolution (distribution of offsets)
        confidence_evolution = {
            "crop_offsets": self.confidence_optimizer.crop_offsets.copy(),
            "region_offsets": self.confidence_optimizer.region_offsets.copy()
        }

        # 4. Learning progress
        learning_progress = {
            "total_updates": total_recs,
            "recommendations_feedback_count": total_recs,
            "knowledge_feedback_count": len(self.store.knowledge),
            "agent_feedback_count": len(self.store.agents),
            "top_schemes": sorted(
                self.recommendation_optimizer.scheme_weights.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "top_advice_categories": sorted(
                self.recommendation_optimizer.advice_weights.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

        return {
            "acceptance_rate": round(acceptance_rate, 4),
            "recommendation_quality": round(quality_score, 2),
            "confidence_evolution": confidence_evolution,
            "learning_progress": learning_progress
        }
