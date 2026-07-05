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
    farmer_category: str = Field("Small", description="Small | Marginal | Medium | Large farmer classification.")
    gender: str = Field("Male", description="Male | Female | Other.")
    caste_category: str = Field("General", description="General | SC | ST | OBC caste category.")
    income_bracket: str = Field("Below 2 Lakh", description="Annual income bracket.")
    has_bank_account: bool = Field(True, description="Whether farmer has a linked bank account.")
    has_aadhaar: bool = Field(True, description="Whether farmer has an Aadhaar card.")
    crop_season: str = Field("Kharif", description="Current growing season: Kharif | Rabi | Zaid.")
    is_tenant: bool = Field(False, description="Whether the farmer is a tenant/sharecropper.")
    is_organic: bool = Field(False, description="Whether the farmer practices organic farming.")
    recent_damage: str | None = Field(None, description="Recent crop damage type if any (Rain, Drought, Pest, etc.).")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata parameters.")
