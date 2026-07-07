import time
from typing import Any, Dict, List

from app.personalization.models import FarmDetails, FarmerProfile
from app.schemas.evidence import BaseEvidence
from pydantic import BaseModel, Field


class PredictiveTwin(BaseModel):
    """
    Consolidated Predictive Digital Twin, encapsulating physical farm properties,
    farmer profiles, dynamic predictions, risk indicators, and proactive alerts.
    """
    farmer_id: str = Field(..., description="Target farmer UUID reference.")
    profile: FarmerProfile = Field(..., description="Linked farmer profile setting.")
    twin: FarmDetails = Field(..., description="Physical details and cropping characteristics.")
    predictions: Dict[str, Any] = Field(default_factory=dict, description="Generated forecasting details.")
    risks: Dict[str, Any] = Field(default_factory=dict, description="Calculated agricultural threat indexes.")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Proactive recommendations based on forecasts.")
    updated_at: float = Field(default_factory=time.time, description="Last update epoch timestamp.")


class DigitalTwinEvidence(BaseEvidence):
    """
    Structured evidence representing predictive twin forecasts and risk models.
    """
    farmer_id: str
    predictions: Dict[str, Any] = Field(default_factory=dict)
    risks: Dict[str, Any] = Field(default_factory=dict)
