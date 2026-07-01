from typing import Any

from pydantic import BaseModel, Field


class GovernmentScheme(BaseModel):
    """
    Agricultural ontology model representing government schemes and benefits.
    """
    scheme_id: str = Field(..., description="Unique scheme reference code.")
    title: str = Field(..., description="Full legal name of the welfare program scheme.")
    authority: str = Field(..., description="Sponsoring agency level (e.g., Central, State).")
    department: str = Field(..., description="Department executing the program.")
    benefits: str = Field(..., description="Description of the financial or material aid offered.")
    eligibility_criteria: list[str] = Field(default_factory=list, description="List of constraints required to qualify.")
    application_process: str = Field(..., description="Step-by-step description of application channels.")
    required_documents: list[str] = Field(default_factory=list, description="Documents required for application.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata parameters.")
