import os

import pytest
from app.core.config import settings
from app.core.container import Container
from app.digital_twin.prediction_engine import PredictionEngine
from app.digital_twin.profile_builder import ProfileBuilder
from app.digital_twin.recommendation_engine import RecommendationEngine
from app.digital_twin.risk_engine import RiskEngine
from app.digital_twin.twin_manager import TwinManager
from app.orchestrator.orchestrator import AgentOrchestrator
from app.personalization.models import FarmDetails, FarmerProfile, LongTermMemory
from app.schemas.requests import ExecutionRequest


from typing import Generator

@pytest.fixture
def temp_twin_db_path() -> Generator[str, None, None]:
    path = "./data/test_predictive_twins.json"
    if os.path.exists(path):
        os.remove(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_twin_profile_building() -> None:
    """Verifies profile state builder maps physical features and conversation contexts correctly."""
    builder = ProfileBuilder()

    profile = FarmerProfile(
        farmer_id="farmer_99",
        name="Ramesh Singh",
        preferred_language="pa",
        experience_level="expert",
        risk_tolerance="high",
        budget_limit=200000.0,
        budget_spent=5000.0
    )
    twin = FarmDetails(
        farmer_id="farmer_99",
        land_size_acres=5.5,
        village="Kila Raipur",
        district="Ludhiana",
        state="Punjab",
        climate_zone="semi-arid",
        irrigation_type="canal"
    )
    memory = LongTermMemory(
        farmer_id="farmer_99",
        conversations=[{"query": "Pest help", "response": "Use neem"}],
        historical_outcomes=[{"crop": "Wheat", "yield_kg": 3000, "success": True}]
    )

    state = builder.build_twin_state(profile, twin, memory)

    assert state["farmer_id"] == "farmer_99"
    assert state["name"] == "Ramesh Singh"
    assert state["language"] == "pa"
    assert state["experience_level"] == "expert"
    assert state["land_size_acres"] == 5.5
    assert state["district"] == "Ludhiana"
    assert state["state"] == "Punjab"
    assert len(state["conversations"]) == 1
    assert len(state["historical_outcomes"]) == 1


def test_twin_predictions() -> None:
    """Verifies crop rotation, water demand, disease matching, and scheme eligibility predictions."""
    engine = PredictionEngine()

    state = {
        "farmer_id": "f_1",
        "land_size_acres": 4.0,
        "irrigation_type": "drip",
        "state": "Punjab",
        "crop_history": [{"crop": "Wheat"}],
        "budget_spent": 10000.0,
        "budget_limit": 100000.0,
        "historical_outcomes": [{"success": True}]
    }

    preds = engine.predict(state)

    # Crop rotation (Wheat should rotate to Rice)
    assert preds["next_crop"] == "Rice"

    # Rice base = 4 * 500000 = 2,000,000 * 1.5 (Rice multiplier) * 0.6 (drip efficiency) = 1,800,000
    assert preds["water_demand_liters"] == 1800000.0

    # Disease probability
    assert preds["disease_probability"]["disease"] == "Rice Blast"

    # Income trend
    assert preds["income_trend"]["trend"] == "upward"

    # New schemes eligibility
    assert "PM-Kisan" in preds["scheme_eligibility_changes"]["eligible_new_schemes"]
    assert "PMFBY" in preds["scheme_eligibility_changes"]["eligible_new_schemes"]


def test_twin_risks() -> None:
    """Verifies weather, crop failure, disease, and financial risk ratings."""
    engine = RiskEngine()

    state = {
        "climate_zone": "semi-arid",
        "irrigation_type": "rainfed",
        "experience_level": "beginner",
        "budget_spent": 80000.0,
        "budget_limit": 100000.0
    }
    predictions = {
        "disease_probability": {"probability": 0.35}
    }

    risks = engine.calculate_risks(state, predictions)

    # semi-arid weather risk = 0.50
    assert risks["weather_risk"] == 0.50

    # Crop failure risk (rainfed + 0.25)
    # 0.50 * 0.8 = 0.40. rainfed = 0.40 + 0.25 = 0.65
    assert risks["crop_failure_risk"] == 0.65

    # Disease risk
    assert risks["disease_risk"] == 0.35

    # Financial risk (beginner + 0.15)
    # 80k/100k = 0.8. beginner = 0.8 + 0.15 = 0.95
    assert risks["financial_risk"] == 0.95

    # Composite recommendation risk
    assert risks["recommendation_risk"] > 0.0


def test_twin_recommendations() -> None:
    """Verifies that proactive recommendations trigger properly based on risk parameters."""
    engine = RecommendationEngine()

    state = {
        "irrigation_type": "rainfed",
        "scheme_history": []
    }
    predictions = {
        "next_crop": "Rice",
        "disease_probability": {"disease": "Rice Blast", "probability": 0.40},
        "scheme_eligibility_changes": {"eligible_new_schemes": ["PM-Kisan"]}
    }
    risks = {
        "crop_failure_risk": 0.65
    }

    recs = engine.generate_proactive_recommendations(state, predictions, risks)

    # Drip irrigation because crop_failure_risk > 0.5 and rainfed
    assert any(r["id"] == "twin_rec_drip_irrigation" for r in recs)

    # Disease spray because probability > 0.3
    assert any(r["id"] == "twin_rec_disease_spraying" for r in recs)

    # Sowing advice
    assert any(r["id"] == "twin_rec_crop_sowing" for r in recs)

    # Scheme apply
    assert any(r["id"] == "twin_rec_apply_pm_kisan" for r in recs)


def test_twin_manager_lifecycle(temp_twin_db_path: str) -> None:
    """Verifies twin loading, caching, disk saving, and text-extraction triggers."""
    import uuid
    fid = f"farmer_twin_{uuid.uuid4().hex[:8]}"
    container = Container(settings)
    manager = TwinManager(container=container, db_path=temp_twin_db_path)

    # Initial get twin (hydrates default farmer properties)
    twin = manager.get_twin(fid)
    assert twin is not None
    assert twin.farmer_id == fid
    assert twin.twin.district == "Ludhiana"

    # Trigger text extraction update
    manager.update_twin_from_interaction(
        farmer_id=fid,
        query="I want to grow rice in Dharwad next season.",
        response="Good choice. Here is the advice."
    )

    # Check updated fields
    updated_twin = manager.get_twin(fid)
    assert updated_twin.twin.district == "Dharwad"
    assert updated_twin.twin.state == "Karnataka"
    assert any(c.get("crop") == "Rice" for c in updated_twin.twin.crop_history)

    # Verify predictions were re-run
    assert updated_twin.predictions["next_crop"] == "Wheat"  # rotation from Rice


@pytest.mark.asyncio
async def test_orchestrator_twin_integration() -> None:
    """Verifies orchestrator injects DigitalTwinEvidence and runs forecasting pipelines."""
    container = Container(settings)

    # Stub executing a query
    req = ExecutionRequest(
        query="Explain PM-Kisan scheme and weather risks in Ludhiana.",
        session_id="farmer_ramesh",
        farmer_id="farmer_ramesh"
    )

    orchestrator = AgentOrchestrator(container)

    res = await orchestrator.execute_query(req)
    assert res.status == "success"

    # Verify that the digital twin was created and updated in the manager
    twin = container.twin_manager.get_twin("farmer_ramesh")
    assert twin is not None

    # Verify that predictions and risks were evaluated
    assert "next_crop" in twin.predictions
    assert "crop_failure_risk" in twin.risks

    # Verify district was updated to Ludhiana via text extraction
    assert twin.twin.district == "Ludhiana"
