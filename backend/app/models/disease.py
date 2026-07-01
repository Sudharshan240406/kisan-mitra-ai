from typing import Any

from pydantic import BaseModel, Field


class Disease(BaseModel):
    """
    Agricultural ontology model representing crop pathology/pest diseases.
    """
    disease_id: str = Field(..., description="Unique pathologicial disease code identifier.")
    name: str = Field(..., description="Common pathological name (e.g., Blast, Rust).")
    pathogen_type: str = Field(..., description="Classification category (Fungal, Bacterial, Viral, Pest, Deficiency).")
    crop_targets: list[str] = Field(..., description="List of Crop IDs susceptible to this pathology.")
    symptoms: list[str] = Field(default_factory=list, description="Visual indicator descriptions.")
    diagnosis_indicators: list[str] = Field(default_factory=list, description="Agronomic check markers.")
    prevention_measures: list[str] = Field(default_factory=list, description="Cultural preventative activities.")
    treatment_chemical: list[str] = Field(default_factory=list, description="Approved chemical control recipes.")
    treatment_organic: list[str] = Field(default_factory=list, description="Organic/biological control methods.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata parameters.")
