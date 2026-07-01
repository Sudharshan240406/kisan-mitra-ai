import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class ConversationMetrics(BaseModel):
    """
    Observability metrics record for a single conversation session.
    """
    conversation_id: str
    duration_seconds: float = 0.0
    state_transitions: int = 0
    clarification_count: int = 0
    policy_interventions: int = 0
    decision_time_ms: float = 0.0
    confidence: float = 0.0
    safety_score: float = 1.0
    escalation_count: int = 0
    response_strategy: str = "Short Response"
    workflow: Optional[str] = None
    capability: Optional[str] = None


class IConversationMetricsCollector(ABC):
    """
    Interface definition for exporting conversation observability logs.
    """
    @abstractmethod
    def record_transition(self, conversation_id: str) -> None:
        pass

    @abstractmethod
    def record_clarification(self, conversation_id: str) -> None:
        pass

    @abstractmethod
    def record_intervention(self, conversation_id: str) -> None:
        pass

    @abstractmethod
    def record_decision(
        self,
        conversation_id: str,
        time_ms: float,
        confidence: float,
        safety_score: float,
        workflow: Optional[str],
        capability: Optional[str]
    ) -> None:
        pass

    @abstractmethod
    def record_escalation(self, conversation_id: str) -> None:
        pass

    @abstractmethod
    def record_response_strategy(self, conversation_id: str, strategy: str) -> None:
        pass

    @abstractmethod
    def finalize_conversation(self, conversation_id: str, start_time: float) -> None:
        pass

    @abstractmethod
    def export_metrics(self) -> dict[str, Any]:
        pass


class ConversationMetricsTracker(IConversationMetricsCollector):
    """
    Concrete observability tracker collecting telemetry details for dialog runs.
    """
    def __init__(self) -> None:
        self._metrics: dict[str, ConversationMetrics] = {}

    def _get_or_create(self, conversation_id: str) -> ConversationMetrics:
        if conversation_id not in self._metrics:
            self._metrics[conversation_id] = ConversationMetrics(conversation_id=conversation_id)
        return self._metrics[conversation_id]

    def record_transition(self, conversation_id: str) -> None:
        m = self._get_or_create(conversation_id)
        m.state_transitions += 1

    def record_clarification(self, conversation_id: str) -> None:
        m = self._get_or_create(conversation_id)
        m.clarification_count += 1

    def record_intervention(self, conversation_id: str) -> None:
        m = self._get_or_create(conversation_id)
        m.policy_interventions += 1

    def record_decision(
        self,
        conversation_id: str,
        time_ms: float,
        confidence: float,
        safety_score: float,
        workflow: Optional[str],
        capability: Optional[str]
    ) -> None:
        m = self._get_or_create(conversation_id)
        m.decision_time_ms = time_ms
        m.confidence = confidence
        m.safety_score = safety_score
        m.workflow = workflow
        m.capability = capability

    def record_escalation(self, conversation_id: str) -> None:
        m = self._get_or_create(conversation_id)
        m.escalation_count += 1

    def record_response_strategy(self, conversation_id: str, strategy: str) -> None:
        m = self._get_or_create(conversation_id)
        m.response_strategy = strategy

    def finalize_conversation(self, conversation_id: str, start_time: float) -> None:
        m = self._get_or_create(conversation_id)
        m.duration_seconds = time.time() - start_time

    def export_metrics(self) -> dict[str, Any]:
        """
        Compiles and formats global session statistics summaries.
        """
        records = list(self._metrics.values())
        if not records:
            return {"total_conversations": 0, "averages": {}}

        total_conversations = len(records)
        avg_duration = sum(r.duration_seconds for r in records) / total_conversations
        avg_transitions = sum(r.state_transitions for r in records) / total_conversations
        total_clarifications = sum(r.clarification_count for r in records)
        total_interventions = sum(r.policy_interventions for r in records)
        total_escalations = sum(r.escalation_count for r in records)

        return {
            "total_conversations": total_conversations,
            "averages": {
                "duration_seconds": avg_duration,
                "state_transitions": avg_transitions
            },
            "aggregates": {
                "total_clarifications": total_clarifications,
                "total_policy_interventions": total_interventions,
                "total_escalations": total_escalations
            }
        }
