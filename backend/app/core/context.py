from typing import Any

from pydantic import BaseModel, Field


class AgentContext(BaseModel):
    """
    Standardized execution context propagated down the multi-agent runtime.
    """
    request_id: str = Field(..., description="Unique request identification token.")
    trace_id: str = Field(..., description="Tracing identifier to track request execution logs.")
    session_id: str = Field(..., description="Farmer session ID tracking session state.")
    farmer_id: str | None = Field(default=None, description="Database reference identifier for the farmer.")
    language: str = Field("en", description="Target vernacular ISO code for advisory responses.")
    crop: str | None = Field(default=None, description="Target crop profile related to the advisory query.")
    location: str | None = Field(default=None, description="Location code or geolocation coordinates.")
    season: str | None = Field(default=None, description="Current meteorological or agricultural season.")
    conversation_history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Chronological record of recent chat message exchanges."
    )
    shared_memory: dict[str, Any] = Field(
        default_factory=dict,
        description="Transient memory dict shared among agents during a single workflow run."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary execution context tags."
    )
