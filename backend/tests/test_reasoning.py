import time

from app.intelligence.arm import AgriculturalReasoningMemory, ReasoningMemoryRecord
from app.intelligence.confidence import ConfidenceAggregator
from app.intelligence.decision import (
    ConsensusDecision,
    DecisionEngine,
    FutureLLMDecision,
    HybridDecision,
    WeightedEvidenceDecision,
)
from app.intelligence.reasoning_graph import ReasoningGraph, ReasoningNode
from app.intelligence.safety import SafetyGuard
from app.intelligence.workflow import WorkflowEngine
from app.schemas.evidence import BaseEvidence, WeatherEvidence


def test_evidence_framework():
    # 1. BaseEvidence serialization check
    ev = WeatherEvidence(
        id="ev-w1",
        source="OpenWeatherAPI",
        agent="WeatherAgent",
        timestamp=time.time(),
        confidence=0.9,
        weight=1.0,
        reasoning="Temperature reads 32C",
        temperature=32.0,
        ontology_references=["weather_metrics"]
    )
    assert ev.confidence == 0.9
    assert ev.temperature == 32.0

def test_confidence_engine():
    aggregator = ConfidenceAggregator(penalty_per_missing=0.1)

    ev1 = BaseEvidence(id="ev-1", source="S1", agent="A1", confidence=0.8, weight=1.0, reasoning="Advice 1")
    ev2 = BaseEvidence(id="ev-2", source="S2", agent="A2", confidence=0.9, weight=2.0, reasoning="Advice 2")

    # Calculate: weighted average = (0.8*1.0 + 0.9*2.0)/(1.0+2.0) = (0.8 + 1.8)/3.0 = 2.6/3.0 = 0.866
    report = aggregator.calculate_confidence([ev1, ev2], missing_fields=["crop"])

    assert abs(report.decision_confidence - 0.866) < 0.01
    # Overall confidence = 0.866 - 0.1 (penalty) = 0.766
    assert abs(report.overall_confidence - 0.766) < 0.01
    assert report.missing_penalty == 0.1

def test_safety_guard():
    guard = SafetyGuard(confidence_threshold=0.6)

    ev = BaseEvidence(id="ev-1", source="S1", agent="A1", confidence=0.9, weight=1.0, reasoning="Advice 1", validation_state="valid")

    # Safe assessment
    res_safe = guard.assess([ev], overall_confidence=0.8)
    assert res_safe.is_safe is True
    assert res_safe.risk_score == 0.0

    # Unsafe due to low confidence
    res_unsafe = guard.assess([ev], overall_confidence=0.4)
    assert res_unsafe.is_safe is False
    assert "confidence" in res_unsafe.flagged_reasons[0]
    assert res_unsafe.risk_score == 0.4

    # Unsafe due to invalid validation state
    ev_invalid = BaseEvidence(id="ev-2", source="S2", agent="A2", confidence=0.9, weight=1.0, reasoning="Advice 2", validation_state="invalid")
    res_invalid = guard.assess([ev_invalid], overall_confidence=0.8)
    assert res_invalid.is_safe is False
    assert "invalid" in res_invalid.flagged_reasons[0]

def test_reasoning_graph():
    graph = ReasoningGraph(graph_id="test-g", root_node_id="root")

    n_root = ReasoningNode(node_id="root", node_type="Query")
    n_intent = ReasoningNode(node_id="intent", parent_id="root", node_type="Intent")
    n_agent = ReasoningNode(node_id="agent-node", parent_id="intent", node_type="Agent")

    graph.add_node(n_root)
    graph.add_node(n_intent)
    graph.add_node(n_agent)

    # BFS Traversal
    ordered = graph.traverse()
    assert [n.node_id for n in ordered] == ["root", "intent", "agent-node"]

    # Validation checks
    assert graph.validate_graph() is True

    # Cyclic check
    n_root.parent_id = "agent-node"
    graph.add_node(n_root) # adds cyclic parent pointer
    assert graph.validate_graph() is False

def test_arm_memory():
    arm = AgriculturalReasoningMemory()

    record = ReasoningMemoryRecord(
        decision_id="DEC-1",
        evidence_used=[],
        reasoning_path=["Reasoning step"],
        reasoning_graph={},
        decision_strategy="RuleBased",
        confidence=0.9,
        risk=0.0,
        trace_id="TRC-1",
        outcome="Summary text",
        supporting_agents=["A1"]
    )

    arm.save_record(record)
    fetched = arm.get_record("DEC-1")
    assert fetched.decision_strategy == "RuleBased"

def test_workflow_loader():
    # Verify that engine boots and loads configuration workflows.json
    engine = WorkflowEngine()
    health = engine.health_check()
    assert health["registered_count"] > 1
    assert "weather_workflow" in health["workflow_ids"]

async def test_decision_engine():
    arm = AgriculturalReasoningMemory()
    strategy = WeightedEvidenceDecision()
    engine = DecisionEngine(strategy, arm)

    ev = BaseEvidence(
        id="ev-w",
        source="WeatherAPI",
        agent="Weather",
        confidence=0.9,
        weight=1.0,
        reasoning="Weather indicates rainfall expected."
    )

    rec = await engine.evaluate(
        evidence_list=[ev],
        missing_fields=[],
        trace_id="TRC-TEST",
        session_id="SES-TEST"
    )

    assert rec.summary == "Weighted multi-agent consolidated recommendation."
    assert "Weather" in rec.recommendation
    assert rec.confidence == 0.9
    assert len(arm.list_records()) == 1

async def test_consensus_decision_strategy():
    arm = AgriculturalReasoningMemory()
    strategy = ConsensusDecision()
    engine = DecisionEngine(strategy, arm)

    ev = BaseEvidence(
        id="ev-c1",
        source="WeatherAPI",
        agent="Weather",
        confidence=0.9,
        weight=1.0,
        reasoning="Moderate rain is forecast.",
        validation_state="valid"
    )

    rec = await engine.evaluate(
        evidence_list=[ev],
        missing_fields=[],
        trace_id="TRC-TEST-CONSENSUS",
        session_id="SES-TEST-CONSENSUS"
    )

    assert rec.summary == "Consensus multi-agent verified recommendation."
    assert "Consensus advisory from Weather" in rec.recommendation
    assert rec.confidence == 0.9

async def test_hybrid_decision_strategy():
    arm = AgriculturalReasoningMemory()
    strategy = HybridDecision()
    engine = DecisionEngine(strategy, arm)

    ev1 = BaseEvidence(
        id="ev-h1",
        source="WeatherAPI",
        agent="Weather",
        confidence=0.95,
        weight=1.0,
        reasoning="Weather is good."
    )
    ev2 = BaseEvidence(
        id="ev-h2",
        source="MarketAPI",
        agent="Market",
        confidence=0.8,
        weight=0.5,
        reasoning="Market prices are rising."
    )

    rec = await engine.evaluate(
        evidence_list=[ev1, ev2],
        missing_fields=[],
        trace_id="TRC-TEST-HYBRID",
        session_id="SES-TEST-HYBRID"
    )

    assert rec.summary == "Hybrid prioritized multi-agent recommendation."
    assert "[CRITICAL] (Weather" in rec.recommendation
    assert "[General] (Market" in rec.recommendation

async def test_future_llm_decision_strategy():
    arm = AgriculturalReasoningMemory()
    strategy = FutureLLMDecision()
    engine = DecisionEngine(strategy, arm)

    ev = BaseEvidence(
        id="ev-l1",
        source="WeatherAPI",
        agent="Weather",
        confidence=0.9,
        weight=1.0,
        reasoning="Clear skies forecast."
    )

    rec = await engine.evaluate(
        evidence_list=[ev],
        missing_fields=[],
        trace_id="TRC-TEST-LLM",
        session_id="SES-TEST-LLM"
    )

    assert "LLM synthesized" in rec.summary or "Simulated LLM" in rec.summary
    assert "Clear skies forecast" in rec.recommendation

