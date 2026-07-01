"""
Kisan Mitra AI — Personalization API Router
===========================================
Defines the REST endpoints for managing farmer profiles, digital twins,
memories, scheduled task alerts, feedback loops, and operations dashboards.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.container import Container
from app.dependencies.container import get_container
from app.personalization.models import (
    FarmerProfile,
    FarmDetails,
    LongTermMemory,
    PrivacyConsent,
    Reminder,
)

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
