from typing import Any

from pydantic import BaseModel, Field


class Farmer(BaseModel):
    """
    Core ontology model representing a Farmer profile.
    """
    farmer_id: str = Field(..., description="Unique profile tracker identifier.")
    name: str = Field(..., description="Full legal name of the farmer.")
    phone_number: str = Field(..., description="Contact E.164 phone number.")
    state: str = Field(..., description="State region residency designation.")
    district: str = Field(..., description="District region residency designation.")
    preferred_language: str = Field("en", description="Vernacular ISO language code selection.")
    land_size_hectares: float = Field(..., description="Total cultivated land size metric.")
    soil_type: str | None = Field(None, description="Soil class characteristics description.")
    water_source: str | None = Field(None, description="Irrigation water source (e.g., Borewell, Rainfed).")
    active_crops: list[str] = Field(default_factory=list, description="List of Crop IDs currently planted.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata parameters.")
