from app.orchestrator.planner import DynamicPlanner
from app.orchestrator.response_builder import ResponseBuilder
from app.orchestrator.router import IntentRouter
from app.orchestrator.validator import ResponseValidator


def test_intent_router_classification():
    router = IntentRouter()

    # Test Government Scheme
    res = router.detect_intent("Tell me about pm-kisan yojana eligibility")
    assert res["intent"] == "Government Scheme"
    assert res["confidence"] == 0.95

    # Test Weather
    res = router.detect_intent("Is it going to rain in Punjab tomorrow?")
    assert res["intent"] == "Weather"
    assert "location:punjab" in res["entities"]

    # Test Greeting
    res = router.detect_intent("Namaste Kisan Mitra!")
    assert res["intent"] == "Greeting"

    # Test Fallback
    res = router.detect_intent("What is the soil quality index?")
    assert res["intent"] == "General Question"

def test_dynamic_planner_selection():
    planner = DynamicPlanner()

    # Weather
    agents = planner.select_agents("Weather")
    assert "Weather" in agents
    assert "Knowledge" in agents

    # Government Scheme
    agents = planner.select_agents("Government Scheme")
    assert "GovernmentScheme" in agents
    assert "LLM" in agents

def test_response_validator_warnings():
    validator = ResponseValidator()

    # Low confidence warning
    warnings = validator.validate({"confidence": 0.5, "recommendation": "Try organic farming"})
    assert any("Low confidence" in w for w in warnings)

    # Contradiction warning
    warnings = validator.validate({
        "confidence": 0.9,
        "recommendation": "You are eligible for PM-Kisan but not eligible for PM-Kisan benefit."
    })
    assert any("Potential contradiction" in w for w in warnings)

def test_response_builder_structure():
    builder = ResponseBuilder()
    rec = builder.build_trusted_recommendation(
        summary="PM-Kisan fit",
        recommendation="Apply at registry",
        confidence=0.98,
        reasoning=["Check size", "Verify bank"],
        sources=["registry_db"],
        evidence=[],
        warnings=[],
        missing_information=[],
        follow_up_required=[],
        safety_assessment={"risk_score": 0.0},
        reasoning_graph_ref="REF-123"
    )
    assert rec["summary"] == "PM-Kisan fit"
    assert rec["confidence"] == 0.98
    assert rec["reasoning_graph_ref"] == "REF-123"
