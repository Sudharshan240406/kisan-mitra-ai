from typing import Any

from pydantic import BaseModel, Field


class EligibilityRule(BaseModel):
    """A single structured eligibility criterion for a government scheme."""
    field: str = Field(..., description="Farmer profile field to evaluate (e.g., 'land_size_hectares').")
    operator: str = Field(..., description="Comparison operator: eq, ne, lt, lte, gt, gte, in, not_in, exists, any.")
    value: Any = Field(default=None, description="Expected value or list of values for comparison.")
    description: str = Field("", description="Human-readable explanation of this rule.")
    required: bool = Field(default=True, description="If True, failing this rule marks NOT_ELIGIBLE.")


class SchemeRecommendation(BaseModel):
    """Output of the eligibility engine for a single scheme."""
    scheme_id: str
    title: str
    status: str = Field(..., description="ELIGIBLE | POSSIBLY_ELIGIBLE | NEED_MORE_INFO | NOT_ELIGIBLE")
    confidence: float = Field(default=0.0, description="0.0 to 1.0 confidence score.")
    reasoning: list[str] = Field(default_factory=list, description="Step-by-step reasoning chain.")
    evidence: list[str] = Field(default_factory=list, description="Evidence sources used.")
    benefits: str = ""
    required_documents: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    deadline: str = ""
    department: str = ""
    helpline: str = ""
    nearest_office: str = ""
    official_url: str = ""
    application_steps: list[str] = Field(default_factory=list)
    expected_timeline: str = ""
    missing_info: list[str] = Field(default_factory=list, description="Farmer fields that need to be collected.")


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
    eligibility_rules: list[EligibilityRule] = Field(default_factory=list, description="Structured machine-evaluable rules.")
    application_process: str = Field(..., description="Step-by-step description of application channels.")
    application_steps: list[str] = Field(default_factory=list, description="Ordered steps for application.")
    required_documents: list[str] = Field(default_factory=list, description="Documents required for application.")
    deadline: str = Field("", description="Application deadline or window.")
    helpline: str = Field("", description="Government helpline number.")
    nearest_office: str = Field("", description="Type of nearest office for application.")
    official_url: str = Field("", description="Official website URL.")
    state_applicability: list[str] = Field(default_factory=list, description="Applicable states (empty = all India).")
    farmer_categories: list[str] = Field(default_factory=list, description="Applicable farmer categories.")
    gender_specific: str = Field("", description="If gender-specific, which gender. Empty = all.")
    caste_categories: list[str] = Field(default_factory=list, description="Applicable caste categories (empty = all).")
    crop_specific: list[str] = Field(default_factory=list, description="Applicable crops (empty = all).")
    tags: list[str] = Field(default_factory=list, description="Search tags for matching.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata parameters.")
