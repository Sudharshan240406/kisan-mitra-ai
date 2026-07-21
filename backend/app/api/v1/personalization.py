"""
Kisan Mitra AI — Personalization API Router
===========================================
Defines the REST endpoints for managing farmer profiles, digital twins,
memories, scheduled task alerts, feedback loops, and operations dashboards.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from app.core.container import Container
from app.dependencies.container import get_container
from app.personalization.models import (
    FarmDetails,
    FarmerProfile,
    LongTermMemory,
    PrivacyConsent,
    Reminder,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/personalization", tags=["Farmer Personalization"])
logger = logging.getLogger("kisan_mitra_ai.personalization.api")


# ── Request / Response Envelopes ──────────────────────────────────────────

class FeedbackRequest(BaseModel):
    farmer_id: str
    recommendation_id: str
    rating: int
    comment: str = ""


# ── REST Routes ───────────────────────────────────────────────────────────

@router.get("/profile/{farmer_id}", response_model=FarmerProfile)
def get_profile(farmer_id: str, container: Container = Depends(get_container)) -> FarmerProfile:
    svc = container.personalization_platform.registry.get("profile_manager")
    profile = svc.get_profile(farmer_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farmer profile '{farmer_id}' not found."
        )
    return profile


@router.post("/profile", response_model=FarmerProfile)
def create_or_update_profile(profile: FarmerProfile, container: Container = Depends(get_container)) -> FarmerProfile:
    svc = container.personalization_platform.registry.get("profile_manager")
    return svc.create_or_update_profile(profile)


@router.get("/twin/{farmer_id}", response_model=FarmDetails)
def get_twin(farmer_id: str, container: Container = Depends(get_container)) -> FarmDetails:
    svc = container.personalization_platform.registry.get("digital_twin")
    twin = svc.get_twin(farmer_id)
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Digital twin features for '{farmer_id}' not found."
        )
    return twin


@router.post("/twin", response_model=FarmDetails)
def update_twin(twin: FarmDetails, container: Container = Depends(get_container)) -> FarmDetails:
    svc = container.personalization_platform.registry.get("digital_twin")
    return svc.update_twin(twin)


@router.get("/memory/{farmer_id}", response_model=LongTermMemory)
def get_memory(farmer_id: str, container: Container = Depends(get_container)) -> LongTermMemory:
    svc = container.personalization_platform.registry.get("long_term_memory")
    memory = svc.get_memory(farmer_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Long-term memory for '{farmer_id}' not found."
        )
    return memory


@router.post("/memory/feedback")
def log_feedback_and_learn(request: FeedbackRequest, container: Container = Depends(get_container)) -> dict[str, Any]:
    memory_svc = container.personalization_platform.registry.get("long_term_memory")
    learning_svc = container.personalization_platform.registry.get("continuous_learning")

    # 1. Log the feedback
    memory_svc.log_feedback(
        farmer_id=request.farmer_id,
        rec_id=request.recommendation_id,
        rating=request.rating,
        comment=request.comment
    )

    # 2. Trigger learning adjustment loop
    learning_result = learning_svc.run_learning_iteration(request.farmer_id)

    # 3. Trigger new LearningManager updates (Task 8)
    try:
        accepted = request.rating >= 4
        rejected = request.rating <= 2
        ignored = request.rating == 3

        profile_svc = container.personalization_platform.registry.get("profile_manager")
        profile = profile_svc.get_profile(request.farmer_id)

        crop = None
        region = None
        lang = "en"

        if profile:
            lang = profile.preferred_language or "en"
            region = f"{profile.district}, {profile.state}" if profile.district else profile.state
            crop_hist = profile.crop_history
            if crop_hist:
                crop = crop_hist[0]

        context_data = {
            "crop": crop,
            "region": region,
            "language": lang
        }

        feedback_data = {
            "accepted": accepted,
            "rejected": rejected,
            "ignored": ignored,
            "manual_correction": request.comment if rejected else None
        }

        container.learning_manager.process_interaction(
            farmer_id=request.farmer_id,
            recommendation_id=request.recommendation_id,
            context=context_data,
            feedback_data=feedback_data
        )
    except Exception as le_err:
        logger.warning(f"Failed to process learning iteration: {le_err}")

    return {
        "status": "success",
        "feedback_saved": True,
        "learning_loop": learning_result
    }


@router.get("/reminders/{farmer_id}", response_model=List[Reminder])
def get_reminders(
    farmer_id: str, status_filter: Optional[str] = None, container: Container = Depends(get_container)
) -> List[Reminder]:
    svc = container.personalization_platform.registry.get("reminder_scheduler")
    return svc.get_reminders(farmer_id, status_filter)


@router.post("/reminders", response_model=Reminder)
def schedule_reminder(reminder: Reminder, container: Container = Depends(get_container)) -> Reminder:
    svc = container.personalization_platform.registry.get("reminder_scheduler")
    return svc.schedule_reminder(reminder)


@router.post("/reminders/{farmer_id}/{reminder_id}/dismiss")
def dismiss_reminder(farmer_id: str, reminder_id: str, container: Container = Depends(get_container)) -> dict[str, Any]:
    svc = container.personalization_platform.registry.get("reminder_scheduler")
    success = svc.dismiss_reminder(farmer_id, reminder_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder '{reminder_id}' not found for farmer '{farmer_id}'."
        )
    return {"status": "success", "dismissed": True}


@router.get("/consent/{farmer_id}", response_model=PrivacyConsent)
def get_consent(farmer_id: str, container: Container = Depends(get_container)) -> PrivacyConsent:
    svc = container.personalization_platform.registry.get("privacy_consent")
    consent = svc.get_consent(farmer_id)
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Privacy preferences for '{farmer_id}' not found."
        )
    return consent


@router.post("/consent", response_model=PrivacyConsent)
def update_consent(consent: PrivacyConsent, container: Container = Depends(get_container)) -> PrivacyConsent:
    svc = container.personalization_platform.registry.get("privacy_consent")
    return svc.update_consent(consent)


@router.post("/consent/{farmer_id}/scrub")
def scrub_memory(farmer_id: str, container: Container = Depends(get_container)) -> dict[str, Any]:
    svc = container.personalization_platform.registry.get("privacy_consent")
    success = svc.scrub_farmer_memory(farmer_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Farmer '{farmer_id}' records not found."
        )
    return {"status": "success", "scrubbed": True}


@router.get("/metrics")
def get_platform_metrics(container: Container = Depends(get_container)) -> dict[str, Any]:
    return container.personalization_platform.health()


class OnboardingRequest(BaseModel):
    name: str
    phone_number: str
    preferred_language: str = "hi"
    experience_level: str = "intermediate"
    risk_tolerance: str = "medium"
    budget_limit: float = 100000.0
    land_size_acres: float = 2.0
    village: str = ""
    district: str = ""
    state: str = ""
    climate_zone: str = ""
    irrigation_type: str = "rainfed"


@router.post("/onboard", status_code=status.HTTP_201_CREATED)
def onboard_farmer(request: OnboardingRequest, container: Container = Depends(get_container)) -> dict[str, Any]:
    import re
    clean_name = re.sub(r'[^a-zA-Z0-9]', '', request.name.lower())
    clean_phone = re.sub(r'[^0-9]', '', request.phone_number)
    farmer_id = f"farmer_{clean_name}_{clean_phone[:4]}" if clean_name else f"farmer_{clean_phone[:8]}"

    # Get services
    profile_svc = container.personalization_platform.registry.get("profile_manager")
    twin_svc = container.personalization_platform.registry.get("digital_twin")
    consent_svc = container.personalization_platform.registry.get("privacy_consent")

    # Create profile
    profile = FarmerProfile(
        farmer_id=farmer_id,
        name=request.name,
        preferred_language=request.preferred_language,
        experience_level=request.experience_level,
        risk_tolerance=request.risk_tolerance,
        budget_limit=request.budget_limit,
        budget_spent=0.0,
        farm_goals=["Increase crop yield"],
    )
    profile_svc.create_or_update_profile(profile)

    # Create twin
    twin = FarmDetails(
        farmer_id=farmer_id,
        land_size_acres=request.land_size_acres,
        village=request.village,
        district=request.district,
        state=request.state,
        climate_zone=request.climate_zone,
        crop_zone="General Crop Zone",
        crop_history=[],
        soil_history=[],
        equipment=[],
        livestock=[],
        irrigation_type=request.irrigation_type,
        scheme_history=[],
    )
    twin_svc.update_twin(twin)

    # Set default consent
    consent = PrivacyConsent(
        farmer_id=farmer_id,
        consent_given=True,
        data_retention_days=365,
        memory_controls={},
        personalization_settings={},
        privacy_preferences={}
    )
    consent_svc.update_consent(consent)

    return {
        "status": "success",
        "farmer_id": farmer_id,
        "message": f"Farmer '{request.name}' successfully onboarded with ID '{farmer_id}'."
    }


@router.get("/learning/analytics")
def get_learning_analytics(container: Container = Depends(get_container)) -> dict[str, Any]:
    """
    Exposes continuous learning engine metrics and analytics.
    """
    return container.learning_manager.get_analytics()


@router.get("/twin/{farmer_id}/predictive")
def get_predictive_twin(farmer_id: str, container: Container = Depends(get_container)) -> dict[str, Any]:
    """
    Retrieves the full Predictive Digital Twin state.
    """
    twin = container.twin_manager.get_twin(farmer_id)
    if not twin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Predictive Twin for '{farmer_id}' not found."
        )
    return twin.model_dump()


@router.get("/twin/{farmer_id}/predict")
def run_twin_predictions(farmer_id: str, container: Container = Depends(get_container)) -> dict[str, Any]:
    """
    Runs and returns digital twin forecasts.
    """
    return container.twin_manager.predict(farmer_id)


@router.get("/twin/{farmer_id}/risk")
def run_twin_risks(farmer_id: str, container: Container = Depends(get_container)) -> dict[str, Any]:
    """
    Runs and returns digital twin risk assessments.
    """
    return container.twin_manager.calculate_risk(farmer_id)


@router.get("/twin/{farmer_id}/recommendations")
def get_proactive_recommendations(farmer_id: str, container: Container = Depends(get_container)) -> list[dict[str, Any]]:
    """
    Retrieves proactive recommendations generated from the digital twin forecasting.
    """
    return container.twin_manager.generate_recommendations(farmer_id)


@router.get("/autonomous/history")
def get_notification_history(container: Container = Depends(get_container)) -> list[dict[str, Any]]:
    """
    Retrieves the complete dispatched notification logs history.
    """
    return container.autonomous_manager.notification_engine.history


@router.post("/autonomous/trigger/{farmer_id}")
def trigger_autonomous_cycle(farmer_id: str, container: Container = Depends(get_container)) -> dict[str, Any]:
    """
    Manually triggers an autonomous monitoring cycle for a target farmer.
    """
    return container.autonomous_manager.run_monitoring_cycle(farmer_id)
