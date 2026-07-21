import os
from typing import Any

import pytest
from app.core.container import Container
from app.learning.confidence_optimizer import ConfidenceOptimizer
from app.learning.feedback_store import (
    AgentFeedback,
    FeedbackStore,
    KnowledgeFeedback,
    RecommendationFeedback,
)
from app.learning.learning_manager import LearningManager
from app.learning.ranking_engine import RankingEngine
from app.learning.recommendation_optimizer import RecommendationOptimizer
from app.orchestrator.orchestrator import AgentOrchestrator
from app.schemas.requests import ExecutionRequest


@pytest.fixture
def temp_db_path() -> str:
    path = "./data/test_learning_feedback.json"
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_feedback_store_persistence(temp_db_path: str) -> None:
    """Verifies that feedbacks are correctly written to and loaded from disk."""
    store = FeedbackStore(db_path=temp_db_path)

    rec_fb = RecommendationFeedback(
        farmer_id="farmer_123",
        recommendation_id="rec_abc",
        accepted=True,
        metadata={"crop": "wheat", "region": "Punjab"}
    )
    k_fb = KnowledgeFeedback(
        doc_id="doc_1",
        action="useful"
    )
    a_fb = AgentFeedback(
        agent_name="PestAgent",
        success=True,
        latency_ms=120.5,
        retry_count=1
    )

    store.add_recommendation_feedback(rec_fb)
    store.add_knowledge_feedback(k_fb)
    store.add_agent_feedback(a_fb)

    # Check state and file existence
    assert len(store.recommendations) == 1
    assert len(store.knowledge) == 1
    assert len(store.agents) == 1
    assert os.path.exists(temp_db_path)

    # Reload store
    store2 = FeedbackStore(db_path=temp_db_path)
    assert len(store2.recommendations) == 1
    assert store2.recommendations[0].farmer_id == "farmer_123"
    assert store2.recommendations[0].accepted is True
    assert store2.knowledge[0].doc_id == "doc_1"
    assert store2.agents[0].agent_name == "PestAgent"


def test_confidence_optimizer() -> None:
    """Verifies confidence score tuning and crop/region offsets."""
    optimizer = ConfidenceOptimizer()

    # Baseline
    assert optimizer.get_optimized_confidence(0.70, crop="cotton", region="Gujarat") == 0.70

    # Accept feedback
    fb_accept = RecommendationFeedback(
        farmer_id="farmer_1",
        recommendation_id="rec_1",
        accepted=True,
        metadata={"crop": "cotton", "region": "Gujarat"}
    )

    # Direct tuning check
    assert optimizer.optimize_confidence(0.80, fb_accept) == 0.85

    # Verify offset was applied
    assert optimizer.crop_offsets["cotton"] == 0.02
    assert optimizer.region_offsets["Gujarat"] == 0.02

    # Check optimized output with offsets applied
    assert optimizer.get_optimized_confidence(0.70, crop="cotton", region="Gujarat") == 0.74

    # Reject feedback
    fb_reject = RecommendationFeedback(
        farmer_id="farmer_1",
        recommendation_id="rec_1",
        rejected=True,
        metadata={"crop": "cotton", "region": "Gujarat"}
    )
    assert optimizer.optimize_confidence(0.80, fb_reject) == 0.70

    # Check offsets after rejection
    assert optimizer.crop_offsets["cotton"] == pytest.approx(-0.03) # 0.02 - 0.05
    assert optimizer.region_offsets["Gujarat"] == pytest.approx(-0.03)


def test_recommendation_optimizer_and_ranking() -> None:
    """Verifies preference weights adjustments and recommendation ranking list sorting."""
    optimizer = RecommendationOptimizer()
    ranking_engine = RankingEngine(optimizer=optimizer)

    candidates = [
        {"id": "scheme_pm_kisan", "category": "subsidy", "score": 0.60},
        {"id": "scheme_pmfby", "category": "insurance", "score": 0.50},
    ]
    context = {"region": "Punjab", "language": "pa"}

    # Base ranking without preferences
    ranked = ranking_engine.rank_recommendations(candidates, context)
    assert ranked[0]["id"] == "scheme_pm_kisan"

    # Feed positive signals multiple times to accumulate weights
    fb = RecommendationFeedback(
        farmer_id="f1",
        recommendation_id="scheme_pmfby",
        accepted=True,
        metadata={"scheme": "scheme_pmfby", "advice_type": "insurance", "region": "Punjab", "language": "pa"}
    )
    for _ in range(3):
        optimizer.update_preferences(fb)

    # Re-rank: PMFBY should get boosted and surpass PM-Kisan
    ranked_after = ranking_engine.rank_recommendations(candidates, context)
    assert ranked_after[0]["id"] == "scheme_pmfby"
    assert ranked_after[0]["score"] > 0.50


def test_learning_manager_analytics(temp_db_path: str) -> None:
    """Verifies coordinator logic and analytics calculations."""
    store = FeedbackStore(db_path=temp_db_path)
    manager = LearningManager(store=store)

    context = {"crop": "rice", "region": "Haryana", "language": "hi", "scheme": "pm_kisan"}

    # Interaction 1: Accept
    manager.process_interaction(
        farmer_id="farmer_abc",
        recommendation_id="pm_kisan",
        context=context,
        feedback_data={"accepted": True}
    )

    # Interaction 2: Reject
    manager.process_interaction(
        farmer_id="farmer_abc",
        recommendation_id="pm_kisan",
        context=context,
        feedback_data={"rejected": True}
    )

    # Expose analytics
    analytics = manager.get_analytics()
    assert analytics["acceptance_rate"] == 0.50
    assert analytics["learning_progress"]["total_updates"] == 2
    assert analytics["learning_progress"]["recommendations_feedback_count"] == 2


@pytest.mark.asyncio
async def test_orchestrator_learning_integration() -> None:
    """Verifies orchestrator invokes and tracks telemetry metadata for learning systems."""
    from app.core.config import settings
    container = Container(settings)

    # Register mock specialist agent
    from agents.base import BaseAgent
    from app.schemas.responses import AgentResult

    class MockSpecialistAgent(BaseAgent):
        def __init__(self, llm_provider: Any) -> None:
            super().__init__(name="GovernmentScheme", llm_provider=llm_provider)
        async def initialize(self) -> None:
            pass
        async def execute(self, request: Any, context: Any = None) -> AgentResult:
            return AgentResult(agent_name="GovernmentScheme", content="Mock scheme advice content", confidence=0.9, evidence=[])
        async def health_check(self) -> bool:
            return True
        def validate(self, response: Any) -> list[str]:
            return []
        async def cleanup(self) -> None:
            pass

    mock_agent = MockSpecialistAgent(container.llm_provider)
    await mock_agent.initialize()
    container.registry.register(mock_agent)

    # Instantiate AgentOrchestrator
    orchestrator = AgentOrchestrator(container=container)

    # Inject temporary db to learning manager to avoid writing to default db
    test_db = "./data/test_orchestrator_learning.json"
    if os.path.exists(test_db):
        os.remove(test_db)

    try:
        orchestrator.learning_manager.store = FeedbackStore(db_path=test_db)
        orchestrator.learning_manager.feedback_engine.store = orchestrator.learning_manager.store

        req = ExecutionRequest(
            farmer_id="farmer_test",
            query="Tell me about PM-Kisan scheme.",
            session_id="session_test"
        )

        # Execute query
        resp = await orchestrator.execute_query(req)
        assert resp.status == "success"

        # Check if agent feedback was tracked in store
        store = orchestrator.learning_manager.store
        assert len(store.agents) > 0
        assert any(a.agent_name == "GovernmentScheme" for a in store.agents)
    finally:
        await mock_agent.cleanup()
        if os.path.exists(test_db):
            os.remove(test_db)
        if os.path.exists(test_db):
            os.remove(test_db)
