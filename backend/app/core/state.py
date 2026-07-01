from typing import Any

from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """
    State tracking object capturing execution metadata for an individual agent run.
    """
    status: str = Field(default="idle", description="Current lifecycle state (idle, running, succeeded, failed).")
    confidence: float = Field(default=1.0, description="Confidence score evaluated for the output advisory.")
    execution_time: float = Field(default=0.0, description="Total execution duration metric in milliseconds.")
    start_time: float | None = Field(default=None, description="Starting epoch timestamp.")
    end_time: float | None = Field(default=None, description="Completion epoch timestamp.")
    warnings: list[str] = Field(default_factory=list, description="Non-blocking warning messages encountered.")
    errors: list[str] = Field(default_factory=list, description="Blocking error descriptions.")
    retries: int = Field(default=0, description="Number of execution retry cycles triggered.")
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary execution metrics (e.g., token usage counts, document scan counts)."
    )
