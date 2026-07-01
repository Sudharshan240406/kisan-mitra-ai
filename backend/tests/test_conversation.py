
import pytest
from app.conversation.audit import DecisionAuditRecord, DecisionAuditTrail
from app.conversation.clarification import ClarificationEngine
from app.conversation.context import ConversationContext, ConversationContextManager
from app.conversation.escalation import HumanEscalationManager
from app.conversation.feedback import FeedbackEngine, FeedbackRecord
from app.conversation.observability import ConversationMetricsTracker
from app.conversation.state_machine import ConversationStateMachine
from app.conversation.strategy import (
    InteractionStrategy,
    InteractionStrategyEngine,
    ResponseStrategy,
    ResponseStrategyEngine,
)
from app.intelligence.reasoning_graph import ReasoningGraph, ReasoningNode


@pytest.mark.asyncio
async def test_conversation_state_machine_happy_path() -> None:
    sm = ConversationStateMachine()
    ctx = ConversationContext(conversation_id="c-happy", session_id="s-happy")

    # Start at Greeting
    assert ctx.current_state == "Greeting"

    # process Greeting -> Intent Identification
    next_state = await sm.process_step(ctx)
    assert next_state == "Intent Identification"
    assert ctx.current_state == "Intent Identification"

    # process Intent Identification -> Context Collection
    next_state = await sm.process_step(ctx)
    assert next_state == "Context Collection"

    # process Context Collection -> Missing Information Collection (missing crop)
    next_state = await sm.process_step(ctx)
    assert next_state == "Missing Information Collection"

    # process Missing Information -> Capability Selection (replenished crop)
    next_state = await sm.process_step(ctx)
    assert next_state == "Capability Selection"
    assert ctx.metadata.get("crop") == "Wheat"

    # process Capability Selection -> Workflow Selection
    next_state = await sm.process_step(ctx)
    assert next_state == "Workflow Selection"
    assert ctx.current_capability == "disease_diagnosis"

    # process Workflow Selection -> Reasoning
    next_state = await sm.process_step(ctx)
    assert next_state == "Reasoning"
    assert ctx.current_workflow == "disease_workflow"

    # process Reasoning -> Policy Validation
    next_state = await sm.process_step(ctx)
    assert next_state == "Policy Validation"

    # process Policy Validation -> Recommendation Generation
    next_state = await sm.process_step(ctx)
    assert next_state == "Recommendation Generation"

    # process Recommendation Generation -> Recommendation Confirmation
    next_state = await sm.process_step(ctx)
    assert next_state == "Recommendation Confirmation"

    # process Recommendation Confirmation -> Follow-up Planning
    next_state = await sm.process_step(ctx)
    assert next_state == "Follow-up Planning"

    # process Follow-up Planning -> Conversation Closure
    next_state = await sm.process_step(ctx)
    assert next_state == "Conversation Closure"

    # process Conversation Closure -> None (end of loop)
    next_state = await sm.process_step(ctx)
    assert next_state is None


@pytest.mark.asyncio
async def test_conversation_state_machine_escalation_path() -> None:
    sm = ConversationStateMachine()
    ctx = ConversationContext(conversation_id="c-esc", session_id="s-esc")

    # Transition manually to Escalation
    await sm.transition_to(ctx, "Escalation", "High alert manual handover")
    assert ctx.current_state == "Escalation"

    next_state = await sm.process_step(ctx)
    assert next_state == "Conversation Closure"
    assert ctx.metadata.get("escalation_triggered") is True


def test_conversation_context_serialization() -> None:
    manager = ConversationContextManager()
    ctx = manager.get_or_create_context("conv-101", "sess-101")
    ctx.farmer_id = "FR-FARMER"
    ctx.metadata["test"] = "val"

    serialized = manager.serialize_context("conv-101")
    assert "conv-101" in serialized
    assert "FR-FARMER" in serialized
    assert "test" in serialized

    # Check retrieve singleton
    same_ctx = manager.get_or_create_context("conv-101", "sess-101")
    assert same_ctx.farmer_id == "FR-FARMER"


def test_interaction_strategy_engine() -> None:
    engine = InteractionStrategyEngine()

    # 1. High risk -> Escalation
    strat = engine.select_strategy(
        confidence=0.9, risk=0.9, policy_passed=True, missing_fields=[], evidence_quality=1.0, reasoning_quality=1.0
    )
    assert strat == InteractionStrategy.ESCALATION_PLACEHOLDER

    # 2. Policy failed -> Caution
    strat = engine.select_strategy(
        confidence=0.9, risk=0.2, policy_passed=False, missing_fields=[], evidence_quality=1.0, reasoning_quality=1.0
    )
    assert strat == InteractionStrategy.RECOMMENDATION_WITH_CAUTION

    # 3. Missing fields -> Clarification Required
    strat = engine.select_strategy(
        confidence=0.9, risk=0.1, policy_passed=True, missing_fields=["symptoms"], evidence_quality=1.0, reasoning_quality=1.0
    )
    assert strat == InteractionStrategy.MISSING_INFORMATION_RESPONSE

    # 4. Low confidence -> Low Confidence Response
    strat = engine.select_strategy(
        confidence=0.4, risk=0.1, policy_passed=True, missing_fields=[], evidence_quality=1.0, reasoning_quality=1.0
    )
    assert strat == InteractionStrategy.LOW_CONFIDENCE_RESPONSE

    # 5. High reasoning -> Educational Guidance
    strat = engine.select_strategy(
        confidence=0.8, risk=0.1, policy_passed=True, missing_fields=[], evidence_quality=0.8, reasoning_quality=0.9
    )
    assert strat == InteractionStrategy.EDUCATIONAL_GUIDANCE


def test_response_strategy_engine() -> None:
    engine = ResponseStrategyEngine()

    # Channel adapters tests
    assert engine.resolve_response_format(InteractionStrategy.DIRECT_RECOMMENDATION, "voice") == ResponseStrategy.FUTURE_VOICE_MODE
    assert engine.resolve_response_format(InteractionStrategy.DIRECT_RECOMMENDATION, "sms") == ResponseStrategy.FUTURE_SMS_MODE
    assert engine.resolve_response_format(InteractionStrategy.DIRECT_RECOMMENDATION, "whatsapp") == ResponseStrategy.FUTURE_WHATSAPP_MODE
    assert engine.resolve_response_format(InteractionStrategy.DIRECT_RECOMMENDATION, "mobile") == ResponseStrategy.FUTURE_MOBILE_MODE

    # Direct fallback maps
    assert engine.resolve_response_format(InteractionStrategy.ESCALATION_PLACEHOLDER, "text") == ResponseStrategy.EMERGENCY_PLACEHOLDER
    assert engine.resolve_response_format(InteractionStrategy.EDUCATIONAL_GUIDANCE, "text") == ResponseStrategy.EDUCATIONAL_RESPONSE
    assert engine.resolve_response_format(InteractionStrategy.MISSING_INFORMATION_RESPONSE, "text") == ResponseStrategy.STEP_BY_STEP_GUIDANCE
    assert engine.resolve_response_format(InteractionStrategy.DIRECT_RECOMMENDATION, "text") == ResponseStrategy.SHORT_RESPONSE


def test_clarification_engine() -> None:
    engine = ClarificationEngine()

    # Disease category
    req = engine.generate_request("Disease", ["symptoms", "crop"])
    assert req.category == "Disease"
    assert req.priority_field == "symptoms"
    assert "leaf color changes" in req.guidance_cues["symptoms"]

    # Weather category
    req = engine.generate_request("Weather", ["location"])
    assert req.priority_field == "location"

    # Soil category
    req = engine.generate_request("Soil", ["pH"])
    assert req.priority_field == "pH"


def test_decision_audit_trail() -> None:
    trail = DecisionAuditTrail()
    record = DecisionAuditRecord(
        decision_id="DEC-TEST",
        conversation_id="conv-1",
        workflow_version="1.0.0",
        capability="weather_advisory",
        decision_strategy="RuleBasedDecision",
        policy_version="1.0.0",
        evidence_ids=["ev-1"],
        reasoning_graph_id="graph-1",
        confidence=0.9,
        safety_assessment={"is_safe": True}
    )

    trail.log_record(record)
    resolved = trail.get_record("DEC-TEST")
    assert resolved is not None
    assert resolved.capability == "weather_advisory"

    # Update Outcome
    trail.update_outcome("DEC-TEST", "Crop successfully saved from frost.", "Audited")
    assert trail.get_record("DEC-TEST").future_outcome == "Crop successfully saved from frost."
    assert trail.get_record("DEC-TEST").audit_status == "Audited"


def test_human_escalation_manager() -> None:
    manager = HumanEscalationManager()

    # trigger veterinary specialist
    rec = manager.trigger_escalation(
        conversation_id="conv-123",
        criteria="livestock_symptom",
        reason="Cow has high fever and skin marks.",
        priority="High"
    )
    assert rec.suggested_specialist == "Veterinarian"
    assert rec.priority == "High"

    # trigger agricultural expert
    rec_ag = manager.trigger_escalation(
        conversation_id="conv-123",
        criteria="pest_outbreak",
        reason="Pest infestation in wheat fields.",
        priority="Medium"
    )
    assert rec_ag.suggested_specialist == "Agricultural Expert"


def test_feedback_engine() -> None:
    engine = FeedbackEngine()
    record = FeedbackRecord(
        feedback_id="FB-1",
        conversation_id="conv-1",
        decision_id="DEC-1",
        action_taken="Accepted",
        rating=5,
        farmer_notes="Excellent recommendation!"
    )

    engine.submit_feedback(record)
    feedbacks = engine.get_feedback_by_conversation("conv-1")
    assert len(feedbacks) == 1
    assert feedbacks[0].rating == 5


def test_reasoning_graph_conversation_extensions() -> None:
    graph = ReasoningGraph(graph_id="g-conv-test", root_node_id="root")

    # Add root node
    graph.add_node(ReasoningNode(node_id="root", node_type="Query"))

    # Add conversation nodes
    graph.add_node(ReasoningNode(node_id="n-conv-1", parent_id="root", node_type="Conversation", metadata={"state": "Greeting"}))
    graph.add_node(ReasoningNode(node_id="n-conv-2", parent_id="n-conv-1", node_type="Conversation", metadata={"state": "Context Collection"}))
    graph.add_node(ReasoningNode(node_id="n-dec-1", parent_id="n-conv-2", node_type="Decision", confidence=0.9))

    # Test replays
    conv_replay = graph.replay_conversation()
    assert len(conv_replay) == 2
    assert "Greeting" in conv_replay[0]
    assert "Context Collection" in conv_replay[1]

    reasoning_replay = graph.replay_reasoning()
    assert len(reasoning_replay) == 1
    assert "n-dec-1" in reasoning_replay[0]

    # Test visualization export
    vis_data = graph.get_visualization_metadata()
    assert vis_data["graph_id"] == "g-conv-test"
    assert len(vis_data["nodes"]) == 4
    assert len(vis_data["links"]) == 3


def test_conversation_metrics_tracker() -> None:
    tracker = ConversationMetricsTracker()

    tracker.record_transition("conv-1")
    tracker.record_transition("conv-1")
    tracker.record_clarification("conv-1")
    tracker.record_intervention("conv-1")
    tracker.record_escalation("conv-1")
    tracker.record_response_strategy("conv-1", "Voice Mode")
    tracker.record_decision("conv-1", 150.0, 0.9, 1.0, "weather_workflow", "weather_advisory")

    stats = tracker.export_metrics()
    assert stats["aggregates"]["total_clarifications"] == 1
    assert stats["aggregates"]["total_policy_interventions"] == 1
    assert stats["aggregates"]["total_escalations"] == 1
