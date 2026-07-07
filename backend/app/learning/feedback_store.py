import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.learning.feedback_store")

class RecommendationFeedback(BaseModel):
    """
    Farmer recommendation feedback captured for optimization.
    """
    farmer_id: str
    recommendation_id: str
    accepted: bool = False
    rejected: bool = False
    ignored: bool = False
    manual_correction: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeFeedback(BaseModel):
    """
    Tracks documents utility, citation frequency, and quality checks.
    """
    doc_id: str
    action: str  # 'cited', 'useful', 'ignored', 'low_quality'
    timestamp: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentFeedback(BaseModel):
    """
    Tracks agent execution performance metrics.
    """
    agent_name: str
    success: bool
    latency_ms: float
    retry_count: int
    timestamp: float = Field(default_factory=time.time)


class FeedbackStore:
    """
    In-memory and file-persisted store for user, document, and agent feedbacks.
    """
    def __init__(self, db_path: str = "./data/learning_feedback.json") -> None:
        self.db_path = db_path
        self.recommendations: List[RecommendationFeedback] = []
        self.knowledge: List[KnowledgeFeedback] = []
        self.agents: List[AgentFeedback] = []
        self.load_from_disk()

    def add_recommendation_feedback(self, fb: RecommendationFeedback) -> None:
        self.recommendations.append(fb)
        self.save_to_disk()

    def add_knowledge_feedback(self, fb: KnowledgeFeedback) -> None:
        self.knowledge.append(fb)
        self.save_to_disk()

    def add_agent_feedback(self, fb: AgentFeedback) -> None:
        self.agents.append(fb)
        self.save_to_disk()

    def load_from_disk(self) -> None:
        if not os.path.exists(self.db_path):
            return
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.recommendations = [
                RecommendationFeedback(**item) for item in data.get("recommendations", [])
            ]
            self.knowledge = [
                KnowledgeFeedback(**item) for item in data.get("knowledge", [])
            ]
            self.agents = [
                AgentFeedback(**item) for item in data.get("agents", [])
            ]
            logger.info(f"Loaded {len(self.recommendations)} recommendation feedbacks from disk.")
        except Exception as e:
            logger.error(f"Failed to load feedback store from disk: {e}")

    def save_to_disk(self) -> None:
        try:
            dir_name = os.path.dirname(self.db_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)

            data = {
                "recommendations": [item.model_dump() for item in self.recommendations],
                "knowledge": [item.model_dump() for item in self.knowledge],
                "agents": [item.model_dump() for item in self.agents]
            }
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save feedback store to disk: {e}")

    def clear(self) -> None:
        self.recommendations.clear()
        self.knowledge.clear()
        self.agents.clear()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception as e:
                logger.error(f"Failed to remove DB file: {e}")
