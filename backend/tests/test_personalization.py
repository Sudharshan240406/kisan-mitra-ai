"""
Unit Tests — Personalized Farmer AI Platform (Step 10E)
======================================================
Verifies all core personalization loops:
  - Farmer Profile & Digital Twin management
  - Long-term memory & history updates
  - Reminder scheduler scheduling/dismissing
  - Privacy consent, settings, and memory scrubbing (GDPR/compliance)
  - Continuous learning loops adjusting risk/budget parameters
  - Regional adaptation & climate zone mappings
  - Integration with ChiefReasoningAgent via MemoryEvidence
"""
from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from app.core.container import Container
from app.core.config import settings
from app.core.context import AgentContext
from app.main import app
from app.personalization.models import (
    FarmerProfile,
    FarmDetails,
    LongTermMemory,
    PrivacyConsent,
    Reminder,
)
from app.schemas.requests import ExecutionRequest


@pytest.fixture
def container() -> Container:
    return Container(settings)


@pytest.fixture
def client() -> Any:
    from typing import Generator
    with TestClient(app) as client:
        yield client


# ── Loop 1, 2, 4: Profile & Twin Management Tests ─────────────────────────

def test_profile_and_twin_lifecycle(container: Container) -> None:
    platform = container.personalization_platform
    profile_svc = platform.registry.get("profile_manager")
    twin_svc = platform.registry.get("digital_twin")

    farmer_id = "test_farmer_99"
    profile = FarmerProfile(
        farmer_id=farmer_id,
        name="Lakhwinder Singh",
        preferred_language="hi",
        experience_level="beginner",
        risk_tolerance="high",
        budget_limit=80000.0,
        farm_goals=["Drip irrigation system setup"]
    )

    # 1. Create Profile
    saved_profile = profile_svc.create_or_update_profile(profile)
    assert saved_profile.farmer_id == farmer_id
    assert saved_profile.experience_level == "beginner"

    # 2. Get Profile
    retrieved_profile = profile_svc.get_profile(farmer_id)
    assert retrieved_profile is not None
    assert retrieved_profile.name == "Lakhwinder Singh"

    # 3. Check Auto-created Twin & update details
    twin = twin_svc.get_twin(farmer_id)
    assert twin is not None
    assert twin.farmer_id == farmer_id
    twin.land_size_acres = 4.2
    twin.village = "Mullanpur"
    twin.district = "Ludhiana"
    twin.state = "Punjab"
    twin.equipment = ["Tractor"]
    twin_svc.update_twin(twin)

    updated_twin = twin_svc.get_twin(farmer_id)
    assert updated_twin.land_size_acres == 4.2
    assert updated_twin.village == "Mullanpur"


# ── Loop 3: Long-Term Memory Tests ────────────────────────────────────────

def test_long_term_memory_logging(container: Container) -> None:
    platform = container.personalization_platform
    memory_svc = platform.registry.get("long_term_memory")
    farmer_id = "farmer_ramesh"

    memory = memory_svc.get_memory(farmer_id)
    assert memory is not None
    initial_turns = len(memory.conversations)

    # 1. Log turn
    memory_svc.log_conversation(
        farmer_id=farmer_id,
        query="Should I irrigate today?",
        response="Yes, weather is dry."
    )
    assert len(memory.conversations) == initial_turns + 1

    # 2. Log recommendation
    initial_recs = len(memory.recommendations)
    memory_svc.log_recommendation(
        farmer_id=farmer_id,
        rec_id="REC-TEST-99",
        text="Apply organic compost.",
        confidence=0.92
    )
    assert len(memory.recommendations) == initial_recs + 1
    assert memory.ai_confidence_history[-1] == 0.92


# ── Loop 5: Regional Adaptation Tests ─────────────────────────────────────

def test_regional_adaptation(container: Container) -> None:
    regional_svc = container.personalization_platform.registry.get("regional_intelligence")

    zone = regional_svc.get_agro_climatic_zone("Punjab")
    assert zone == "Trans-Gangetic Plains Region"

    zone_k = regional_svc.get_agro_climatic_zone("Karnataka")
    assert zone_k == "Southern Plateau and Hills Region"

    trans = regional_svc.adapt_vernacular_names("wheat", "hi")
    assert trans == "गेहूं"

    trans_kn = regional_svc.adapt_vernacular_names("wheat", "kn")
    assert trans_kn == "ಗೋಧಿ"


# ── Loop 7: Reminder Scheduler Tests ──────────────────────────────────────

def test_reminder_scheduler(container: Container) -> None:
    platform = container.personalization_platform
    reminder_svc = platform.registry.get("reminder_scheduler")
    farmer_id = "farmer_siddappa"

    # 1. Schedule a reminder
    rem = Reminder(
        farmer_id=farmer_id,
        type="harvest",
        message="Harvesting window opens in 2 days.",
        due_date=time.time() + 172800,
        priority="high"
    )
    reminder_svc.schedule_reminder(rem)

    active_reminders = reminder_svc.get_reminders(farmer_id, status_filter="pending")
    assert any(r.reminder_id == rem.reminder_id for r in active_reminders)

    # 2. Dismiss
    success = reminder_svc.dismiss_reminder(farmer_id, rem.reminder_id)
    assert success is True

    reminders_after = reminder_svc.get_reminders(farmer_id, status_filter="pending")
    assert not any(r.reminder_id == rem.reminder_id for r in reminders_after)


# ── Loop 8: Continuous Learning Tests ─────────────────────────────────────

def test_continuous_learning_rules(container: Container) -> None:
    platform = container.personalization_platform
    learning_svc = platform.registry.get("continuous_learning")
    memory_svc = platform.registry.get("long_term_memory")
    profile_svc = platform.registry.get("profile_manager")

    farmer_id = "learning_farmer"
    # Create profile with high risk
    profile = FarmerProfile(
        farmer_id=farmer_id,
        name="Learning test",
        preferred_language="en",
        risk_tolerance="high",
        budget_limit=100000.0
    )
    profile_svc.create_or_update_profile(profile)

    # Add negative feedback ratings
    memory_svc.log_feedback(farmer_id, "REC-X1", 1, "Pest control advice was bad")
    memory_svc.log_feedback(farmer_id, "REC-X2", 2, "Soil dosage caused leaf burn")

    # Run learning iteration
    result = learning_svc.run_learning_iteration(farmer_id)
    assert result["status"] == "success"
    
    # Check risk tolerance downgraded to 'low' due to bad outcomes
    updated_profile = profile_svc.get_profile(farmer_id)
    assert updated_profile.risk_tolerance == "low"


# ── Loop 9: Privacy and Consent Tests ─────────────────────────────────────

def test_privacy_scrubbing(container: Container) -> None:
    platform = container.personalization_platform
    privacy_svc = platform.registry.get("privacy_consent")
    memory_svc = platform.registry.get("long_term_memory")

    farmer_id = "farmer_ramesh"

    # Verify data exists initially
    memory = memory_svc.get_memory(farmer_id)
    assert len(memory.conversations) > 0

    # Scrub memory
    success = privacy_svc.scrub_farmer_memory(farmer_id)
    assert success is True

    # Verify it is empty
    scrubbed_memory = memory_svc.get_memory(farmer_id)
    assert len(scrubbed_memory.conversations) == 0
    assert len(scrubbed_memory.recommendations) == 0


# ── Loop 6: Adaptive Reasoning Platform Integration Tests ──────────────────

@pytest.mark.asyncio
async def test_adaptive_reasoning_node_execution(container: Container) -> None:
    from agents.planner.planner import PlannerAgent
    from agents.weather.weather import WeatherAgent
    from agents.market.market import MarketAgent
    from agents.memory.memory import MemoryAgent
    from agents.disease.disease import KnowledgeAgent
    from agents.schemes.schemes import GovernmentSchemeAgent
    from agents.verifier.verifier import VerifierAgent

    # Register all platform agents so orchestrator executes cleanly
    planner_agent = PlannerAgent(container.llm_provider)
    weather_agent = WeatherAgent(container.llm_provider, container.weather_service)
    market_agent = MarketAgent(container.llm_provider, container.market_service)
    memory_agent = MemoryAgent(container.llm_provider, container.memory_service)
    knowledge_agent = KnowledgeAgent(container.llm_provider, container.knowledge_service)
    scheme_agent = GovernmentSchemeAgent(container.llm_provider, container.scheme_service)
    verifier_agent = VerifierAgent(container.llm_provider)

    await planner_agent.initialize()
    await weather_agent.initialize()
    await market_agent.initialize()
    await memory_agent.initialize()
    await knowledge_agent.initialize()
    await scheme_agent.initialize()
    await verifier_agent.initialize()

    container.registry.register(planner_agent)
    container.registry.register(weather_agent)
    container.registry.register(market_agent)
    container.registry.register(memory_agent)
    container.registry.register(knowledge_agent)
    container.registry.register(scheme_agent)
    container.registry.register(verifier_agent)

    from app.orchestrator.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator(container)

    req = ExecutionRequest(
        session_id="farmer_siddappa",
        query="What irrigation advice is recommended for my rice crop?",
        farmer_id="farmer_siddappa"
    )

    response = await orchestrator.execute_query(req)
    assert response.status == "success"
    data = response.data
    assert data is not None
    assert "recommendation" in data
    rec_text = data["recommendation"]
    
    # Verify personalized tag was injected into recommendation
    assert "[PERSONALIZED FOR SIDDAPPA GOWDA]" in rec_text
    assert "Risk: LOW" in rec_text


# ── REST API Router Tests ──────────────────────────────────────────────────

def test_api_personalization_endpoints(client: TestClient) -> None:
    # 1. GET profile
    resp = client.get("/api/v1/personalization/profile/farmer_ramesh")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Ramesh Singh"

    # 2. GET twin
    resp = client.get("/api/v1/personalization/twin/farmer_ramesh")
    assert resp.status_code == 200
    assert resp.json()["state"] == "Punjab"

    # 3. POST feedback
    resp = client.post(
        "/api/v1/personalization/memory/feedback",
        json={
            "farmer_id": "farmer_ramesh",
            "recommendation_id": "REC-RAM-01",
            "rating": 5,
            "comment": "Super effective!"
        }
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

    # 4. GET metrics
    resp = client.get("/api/v1/personalization/metrics")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
