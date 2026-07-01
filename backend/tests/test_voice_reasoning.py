from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.reasoning.chief import ReasoningResult, RiskAssessment
from app.voice.reasoning import VoiceReasoningPipeline
from app.voice.session import FarmerProfileSnapshot, VoiceSession
from app.voice.speech_context import SpeechContext, VoiceIntent


class StubChiefAgent:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    async def reason(self, **kwargs: object) -> ReasoningResult:
        self.calls.append(kwargs)
        return ReasoningResult(
            result_id="RES-VOICE",
            session_id="VS-1",
            trace_id="TRACE-VOICE",
            query=str(kwargs["query"]),
            primary_recommendation="Apply light irrigation tomorrow morning.",
            summary="Irrigate lightly tomorrow morning.",
            suggested_actions=["Check soil moisture before irrigation."],
            alternatives=[],
            risk_assessment=RiskAssessment(
                risk_score=0.2,
                risk_level="low",
                risk_factors=[],
                mitigation_steps=[],
            ),
            warnings=[],
            missing_information=list(kwargs["missing_fields"]),
            evidence_used=[],
            overall_confidence=0.82,
            per_agent_confidence={},
            confidence_interval=(0.72, 0.9),
            calibration_flags=[],
            explanation="Reasoned from available context.",
            reasoning_path=["Top path selected from available evidence."],
            agents_contributing=[],
            assumptions=[],
            consensus_reached=True,
            conflicts_detected=[],
            conflicts_resolved=[],
            escalated=False,
            escalation_reason=None,
            escalation_packet=None,
            reasoning_graph_ref="GRAPH-VOICE",
        )


@pytest.mark.asyncio
async def test_voice_reasoning_pipeline_uses_chief_agent_contract() -> None:
    chief_agent = StubChiefAgent()
    container = SimpleNamespace(chief_agent=chief_agent)
    pipeline = VoiceReasoningPipeline(container)

    session = VoiceSession(call_id="CALL-1", trace_id="TRACE-1")
    session.farmer_profile = FarmerProfileSnapshot(location="Punjab", crops=["wheat"])
    speech_context = SpeechContext(session)
    intent = VoiceIntent(
        intent_type="irrigation",
        raw_query="When should I irrigate my wheat field?",
        crop="wheat",
        location="Punjab",
        confidence=0.9,
    )

    result = await pipeline.reason(intent.raw_query, intent, session, speech_context)

    assert result.advisory_text == "Apply light irrigation tomorrow morning."
    assert result.confidence == 0.82
    assert result.follow_up_reminders == ["Check soil moisture before irrigation."]
    assert result.reasoning_path == ["Top path selected from available evidence."]
    assert chief_agent.calls[0]["parsed_evidence"] == []
    assert chief_agent.calls[0]["crop"] == "wheat"
    assert chief_agent.calls[0]["location"] == "Punjab"


@pytest.mark.asyncio
async def test_voice_reasoning_pipeline_tracks_missing_fields() -> None:
    chief_agent = StubChiefAgent()
    container = SimpleNamespace(chief_agent=chief_agent)
    pipeline = VoiceReasoningPipeline(container)

    session = VoiceSession(call_id="CALL-2", trace_id="TRACE-2")
    speech_context = SpeechContext(session)
    intent = VoiceIntent(
        intent_type="weather",
        raw_query="Will it rain tomorrow?",
        confidence=0.7,
    )

    await pipeline.reason(intent.raw_query, intent, session, speech_context)

    assert chief_agent.calls[0]["missing_fields"] == ["crop", "location"]
