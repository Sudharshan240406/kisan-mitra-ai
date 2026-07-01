
from app.intelligence.analysis import MissingInformationDetector, QueryAnalyzer
from app.intelligence.entity import EntityExtractor, EntityType
from app.intelligence.intent import IntentEngine, IntentType
from app.intelligence.planner import (
    FutureMLPlanner,
    HybridPlanner,
    LLMPlanner,
    RuleBasedPlanner,
)
from app.intelligence.workflow import Workflow, WorkflowRegistry


def test_intent_engine():
    engine = IntentEngine()

    # 1. Weather intent match
    res_w = engine.detect_intents("Is it going to rain today?")
    assert IntentType.WEATHER in res_w.detected_intents
    assert res_w.confidence[IntentType.WEATHER] > 0.0

    # 2. Disease intent match
    res_d = engine.detect_intents("What is this crop spot infection?")
    assert IntentType.DISEASE in res_d.detected_intents

    # 3. Mixed intents match
    res_m = engine.detect_intents("What is the mandi price of wheat and will it rain?")
    assert IntentType.MIXED_QUERY in res_m.detected_intents
    assert IntentType.WEATHER in res_m.detected_intents
    assert IntentType.MARKET in res_m.detected_intents

    # 4. Unknown intent match
    res_u = engine.detect_intents("abcdefgxyz")
    assert IntentType.UNKNOWN in res_u.detected_intents

def test_entity_extraction():
    extractor = EntityExtractor()

    # Extract crop & state
    res = extractor.extract_entities("Will it rain in Punjab on the wheat crop?")
    extracted_values = [e.value for e in res.entities]

    assert "Punjab" in extracted_values
    assert "Wheat" in extracted_values
    assert EntityType.STATE in res.extracted_types
    assert EntityType.CROP in res.extracted_types

def test_missing_information_detector():
    detector = MissingInformationDetector()
    engine = IntentEngine()
    extractor = EntityExtractor()

    # Query with missing crop type
    intents = engine.detect_intents("My plants have yellow spots symptoms")
    entities = extractor.extract_entities("My plants have yellow spots symptoms")
    report = detector.detect_missing(intents, entities)

    assert "crop" in report.missing_fields
    assert report.is_complete is False

    # Weather query with missing location
    intents_w = engine.detect_intents("Will it rain today?")
    entities_w = extractor.extract_entities("Will it rain today?")
    report_w = detector.detect_missing(intents_w, entities_w)

    assert "location" in report_w.missing_fields
    assert report_w.is_complete is False

def test_workflow_registry():
    registry = WorkflowRegistry()

    wf = Workflow(
        workflow_id="test_wf",
        name="Test Workflow",
        description="Testing registry pipelines.",
        steps=["Planner", "Weather"]
    )

    registry.register(wf)
    discovered = registry.discover("test_wf")

    assert discovered.name == "Test Workflow"
    assert len(registry.list_workflows()) == 1

    registry.remove("test_wf")
    assert len(registry.list_workflows()) == 0

async def test_rule_based_planner():
    analyzer = QueryAnalyzer()
    planner = RuleBasedPlanner()

    analysis = analyzer.analyze("Will it rain on my wheat in Amritsar Punjab?")
    plan = await planner.plan(analysis)

    assert plan.workflow_id == "weather_workflow"
    assert "Weather" in plan.required_agents
    assert "WeatherTool" in plan.required_tools
    assert plan.estimated_complexity == "low"


async def test_hybrid_planner():
    analyzer = QueryAnalyzer()
    planner = HybridPlanner()
    analysis = analyzer.analyze("Will it rain on my wheat?")
    plan = await planner.plan(analysis)
    assert "Weather" in plan.required_agents

async def test_llm_planner_fallback():
    analyzer = QueryAnalyzer()
    planner = LLMPlanner()
    analysis = analyzer.analyze("Mandi prices for wheat")
    plan = await planner.plan(analysis)
    assert "Market" in plan.required_agents

async def test_future_ml_planner():
    analyzer = QueryAnalyzer()
    planner = FutureMLPlanner()
    analysis = analyzer.analyze("Will it rain and what are the mandi prices of wheat?")
    plan = await planner.plan(analysis)
    assert "weather" in plan.required_agents
    assert "market" in plan.required_agents
