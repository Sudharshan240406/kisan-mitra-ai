import time
from typing import Any

from pydantic import BaseModel, Field


class ReasoningMemoryRecord(BaseModel):
    """
    Registry item storing reasoning step tracking metadata.
    """
    decision_id: str = Field(..., description="Unique decision execution identifier.")
    evidence_used: list[dict[str, Any]] = Field(..., description="List of evidence objects used during decision aggregation.")
    reasoning_path: list[str] = Field(..., description="The logic path log lines.")
    reasoning_graph: dict[str, Any] = Field(..., description="The exported ReasoningGraph representation dictionary.")
    decision_strategy: str = Field(..., description="Decision strategy name applied.")
    confidence: float = Field(..., description="Calculated overall confidence score.")
    risk: float = Field(..., description="Calculated safety risk rating.")
    timestamp: float = Field(default_factory=time.time, description="Creation timestamp.")
    trace_id: str = Field(..., description="Request trace ID.")
    outcome: str = Field(..., description="The generated TrustedRecommendation summary outcome.")
    supporting_agents: list[str] = Field(..., description="Agents that contributed to this decision record.")

class AgriculturalReasoningMemory:
    """
    In-memory registry storing why a recommendation decision was generated.
    """
    def __init__(self) -> None:
        self._storage: dict[str, ReasoningMemoryRecord] = {}

    def save_record(self, record: ReasoningMemoryRecord) -> None:
        self._storage[record.decision_id] = record
        import logging
        logging.getLogger("kisan_mitra_ai.arm").info(
            f"Saved reasoning decision record '{record.decision_id}' for trace '{record.trace_id}'."
        )

    def get_record(self, decision_id: str) -> ReasoningMemoryRecord | None:
        return self._storage.get(decision_id)

    def list_records(self) -> list[ReasoningMemoryRecord]:
        return list(self._storage.values())

    def clear(self) -> None:
        self._storage.clear()
