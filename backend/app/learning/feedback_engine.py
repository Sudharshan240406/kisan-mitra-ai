import logging
from typing import Any, Dict, Optional

from app.learning.feedback_store import (
    AgentFeedback,
    FeedbackStore,
    KnowledgeFeedback,
    RecommendationFeedback,
)

logger = logging.getLogger("kisan_mitra_ai.learning.feedback_engine")

class FeedbackEngine:
    """
    Registry framework that captures farmer interaction actions, document citation usage,
    and agent performance feedback.
    """
    def __init__(self, store: Optional[FeedbackStore] = None) -> None:
        self.store = store or FeedbackStore()

    def record_recommendation_feedback(
        self,
        farmer_id: str,
        recommendation_id: str,
        accepted: bool = False,
        rejected: bool = False,
        ignored: bool = False,
        manual_correction: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RecommendationFeedback:
        """
        Records farmer outcome feedback (accepted/rejected/ignored) for recommendations.
        """
        fb = RecommendationFeedback(
            farmer_id=farmer_id,
            recommendation_id=recommendation_id,
            accepted=accepted,
            rejected=rejected,
            ignored=ignored,
            manual_correction=manual_correction,
            metadata=metadata or {}
        )
        self.store.add_recommendation_feedback(fb)
        return fb

    def record_knowledge_feedback(
        self,
        doc_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> KnowledgeFeedback:
        """
        Tracks document relevance actions (cited, useful, ignored, low_quality).
        """
        fb = KnowledgeFeedback(
            doc_id=doc_id,
            action=action,
            metadata=metadata or {}
        )
        self.store.add_knowledge_feedback(fb)
        return fb

    def record_agent_feedback(
        self,
        agent_name: str,
        success: bool,
        latency_ms: float,
        retry_count: int
    ) -> AgentFeedback:
        """
        Records performance metrics for specialist agents.
        """
        fb = AgentFeedback(
            agent_name=agent_name,
            success=success,
            latency_ms=latency_ms,
            retry_count=retry_count
        )
        self.store.add_agent_feedback(fb)
        return fb
