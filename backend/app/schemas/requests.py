from typing import Any

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    """
    Standard input structure for executing an individual agent.
    """
    query: str = Field(..., description="The user query or prompt details to be addressed by the agent.")
    context: dict[str, Any] = Field(default_factory=dict, description="Contextual information (farmer profile, geography, historical state).")
    parameters: dict[str, Any] = Field(default_factory=dict, description="LLM parameter overrides or runtime tweaks.")

class PlannerRequest(BaseModel):
    """
    Standard request layout for generating an execution task plan.
    """
    query: str = Field(..., description="The user input query to categorize and generate an execution plan for.")
    farmer_id: str | None = Field(None, description="Optional profile identifier of the associated farmer.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Channel metadata (Web, Voice/IVR, SMS).")

class ExecutionRequest(BaseModel):
    """
    Standard client entry request model sent to the main Orchestrator.
    """
    session_id: str = Field(..., description="Unique session tracking identifier.")
    query: str = Field(..., description="Main user prompt text.")
    trace_enabled: bool = Field(default=False, description="Flag to enable tracing / details log print.")
    farmer_id: str | None = Field(default=None, description="Optional associated farmer profile ID.")
