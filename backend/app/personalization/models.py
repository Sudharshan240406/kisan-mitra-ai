"""
Kisan Mitra AI — Personalization Models
=======================================
Pydantic schemas and domain models for managing farmer profiles,
digital twins, long-term memories, privacy preferences, and alerts.
"""
from __future__ import annotations

import time
import uuid
from typing import Any, Optional
from pydantic import BaseModel, Field


class FarmerProfile(BaseModel):
    """
    Core profile settings and preferences for the farmer.
    """
    farmer_id: str = Field(..., description="Unique farmer identification token.")
    name: str = Field(..., description="Farmer's full name.")
    preferred_language: str = Field(default="hi", description="ISO language preference (e.g., hi, kn, te, ta, en).")
    experience_level: str = Field(default="intermediate", description="Experience category: beginner | intermediate | expert.")
    risk_tolerance: str = Field(default="medium", description="Risk posture: low | medium | high.")
    budget_limit: float = Field(default=100000.0, description="Seasonal budget limit in INR.")
    budget_spent: float = Field(default=0.0, description="Amount of budget spent so far in INR.")
    farm_goals: list[str] = Field(default_factory=list, description="Primary crop or farm objectives.")
    preferences: dict[str, Any] = Field(default_factory=dict, description="Arbitrary preference flags.")


class FarmDetails(BaseModel):
    """
    Physical farm characteristics constituting the Digital Twin.
    """
    farmer_id: str = Field(..., description="Associated farmer profile ID.")
    land_size_acres: float = Field(..., description="Total farm land size in acres.")
    village: str = Field(..., description="Village name.")
    district: str = Field(..., description="District name.")
    state: str = Field(..., description="State name.")
    climate_zone: str = Field(default="unknown", description="Agro-climatic zone classification.")
    crop_zone: str = Field(default="unknown", description="Major cropping pattern zone.")
    crop_history: list[dict[str, Any]] = Field(default_factory=list, description="Historical crops planted and yields.")
    soil_history: list[dict[str, Any]] = Field(default_factory=list, description="Soil chemistry parameters history.")
    equipment: list[str] = Field(default_factory=list, description="Agricultural tools and machinery owned.")
    livestock: list[str] = Field(default_factory=list, description="Animals kept on the farm.")
    irrigation_type: str = Field(default="rainfed", description="Irrigation source: rainfed | canal | tube_well | drip | sprinkler.")
    scheme_history: list[str] = Field(default_factory=list, description="Welfare schemes availed by the farmer.")


class LongTermMemory(BaseModel):
    """
    Chronological context history across multiple sessions.
    """
    farmer_id: str = Field(..., description="Associated farmer ID.")
    conversations: list[dict[str, Any]] = Field(default_factory=list, description="Recent conversation turns log.")
    recommendations: list[dict[str, Any]] = Field(default_factory=list, description="Recommendations issued and status.")
    diseases: list[dict[str, Any]] = Field(default_factory=list, description="Historical crop disease occurrences.")
    weather_events: list[dict[str, Any]] = Field(default_factory=list, description="Weather impacts logged.")
    market_decisions: list[dict[str, Any]] = Field(default_factory=list, description="Commodity sales decisions.")
    feedback_history: list[dict[str, Any]] = Field(default_factory=list, description="Outcome reviews and ratings.")
    ai_confidence_history: list[float] = Field(default_factory=list, description="Confidence levels of recommendations.")
    historical_outcomes: list[dict[str, Any]] = Field(default_factory=list, description="Farming outcome summaries.")


class PrivacyConsent(BaseModel):
    """
    Consent and retention preferences for personal data.
    """
    farmer_id: str = Field(..., description="Associated farmer ID.")
    consent_given: bool = Field(default=True, description="Whether personalization memory logging is enabled.")
    data_retention_days: int = Field(default=365, description="Number of days to store interaction logs.")
    memory_controls: dict[str, Any] = Field(default_factory=dict, description="Custom privacy configurations.")
    personalization_settings: dict[str, Any] = Field(default_factory=dict, description="Toggle individual platform adjustments.")
    privacy_preferences: dict[str, Any] = Field(default_factory=dict, description="Data sharing configurations.")


class Reminder(BaseModel):
    """
    Calendar event or warning alert scheduled for a farmer.
    """
    reminder_id: str = Field(default_factory=lambda: f"REM-{uuid.uuid4().hex[:8].upper()}")
    farmer_id: str = Field(..., description="Target farmer ID.")
    type: str = Field(..., description="Type: sowing | harvest | fertilizer | irrigation | disease_monitoring | scheme_deadline | weather_alert | market_alert")
    message: str = Field(..., description="Human-readable notification text.")
    due_date: float = Field(..., description="Due timestamp (epoch seconds).")
    status: str = Field(default="pending", description="Status: pending | sent | dismissed")
    priority: str = Field(default="medium", description="Priority level: low | medium | high")
    created_at: float = Field(default_factory=time.time)


class PersonalizationContext(BaseModel):
    """
    Aggregated personalization context injected into reasoning operations.
    """
    farmer_id: str = Field(..., description="Target farmer ID.")
    profile: FarmerProfile
    twin: FarmDetails
    memory: LongTermMemory
    consent: PrivacyConsent
    reminders: list[Reminder] = Field(default_factory=list)
