from typing import Any

from pydantic import BaseModel, Field


class Crop(BaseModel):
    """
    Agricultural ontology model representing a crop type.
    """
    crop_id: str = Field(..., description="Unique code identifier for the crop.")
    name: str = Field(..., description="Common vernacular name (e.g., Rice, Wheat).")
    botanical_name: str | None = Field(None, description="Scientific classification name.")
    crop_type: str = Field(..., description="General category (e.g., Cereal, Legume, Cash Crop).")
    season: str = Field(..., description="Sowing/cropping season profile (e.g., Kharif, Rabi).")
    water_requirement: str | None = Field(None, description="Qualitative water requirement (e.g., Low, Medium, High).")
    soil_requirement: str | None = Field(None, description="Preferred soil class (e.g., Clayey, Loamy, Alluvial).")
    optimal_ph_range: tuple[float, float] | None = Field(None, description="Optimal soil pH value limits.")
    growth_duration_days: int | None = Field(None, description="Typical life cycle duration in days.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata parameters.")
