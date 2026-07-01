import time
from typing import Any

from pydantic import BaseModel, Field


class BaseEvidence(BaseModel):
    """
    Base data contract representing structured evidence statements returned by agents.
    """
    id: str = Field(..., description="Unique evidence record identifier.")
    source: str = Field(..., description="Origin source system (e.g. Mandi API, OpenWeather).")
    agent: str = Field(..., description="Name of the worker agent that generated the evidence.")
    timestamp: float = Field(default_factory=time.time, description="Creation timestamp.")
    confidence: float = Field(default=1.0, description="Evidence confidence rating (0.0 to 1.0).")
    weight: float = Field(default=1.0, description="Importance weight assigned to this evidence.")
    reasoning: str = Field(..., description="Explanation of how the evidence was derived.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata properties.")
    ontology_references: list[str] = Field(default_factory=list, description="IDs pointing to ontology models (e.g. Crop, Disease ID).")
    validation_state: str = Field(default="valid", description="Safety state check ('valid', 'invalid', 'low_confidence').")

class WeatherEvidence(BaseEvidence):
    """Evidence details regarding weather forecast measurements."""
    temperature: float | None = None
    rainfall: float | None = None
    humidity: float | None = None

class DiseaseEvidence(BaseEvidence):
    """Evidence details regarding crop pathology symptoms and diagnoses."""
    symptoms: list[str] = Field(default_factory=list)
    pathogen: str | None = None

class MarketEvidence(BaseEvidence):
    """Evidence details regarding mandi price trading ranges."""
    commodity: str | None = None
    modal_price: float | None = None
    market_name: str | None = None

class KnowledgeEvidence(BaseEvidence):
    """Evidence details extracted from RAG reference manuals."""
    citation: str | None = None
    document_title: str | None = None

class GovernmentSchemeEvidence(BaseEvidence):
    """Evidence details matching subsidy programs."""
    scheme_title: str | None = None
    eligibility_matched: bool = True

class MemoryEvidence(BaseEvidence):
    """Evidence details from historical conversation and farmer profile memory states."""
    farmer_id: str | None = None
    historical_patterns: list[str] = Field(default_factory=list)

class EvidenceBundle(BaseModel):
    """
    Consolidated container packaging multiple structured evidence inputs.
    """
    bundle_id: str = Field(..., description="Unique bundle identifier.")
    trace_id: str = Field(..., description="Trace transaction index identifier.")
    evidence_items: list[BaseEvidence] = Field(..., description="List of structured evidence records.")
    timestamp: float = Field(default_factory=time.time, description="Creation timestamp.")
