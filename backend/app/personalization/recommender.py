"""
Kisan Mitra AI — Adaptive Recommendation Engine
===============================================
Bridges the Personalization Platform and the Reasoning Platform. It loads
personalized contexts and formats them as structured reasoning evidence so
personalization never bypasses safety checks.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Optional

from app.core.context import AgentContext
from app.personalization.models import PersonalizationContext
from app.personalization.platform import PersonalizationPlatform
from app.schemas.evidence import MemoryEvidence

logger = logging.getLogger("kisan_mitra_ai.personalization.recommender")


class AdaptiveRecommendationEngine:
    """
    Coordinates personalization context extraction and converts it into structured
    MemoryEvidence for consumption by the ChiefReasoningAgent.
    """
    def __init__(self, platform: PersonalizationPlatform) -> None:
        self.platform = platform

    def generate_personalization_evidence(
        self, farmer_id: str, context: Optional[AgentContext] = None
    ) -> Optional[MemoryEvidence]:
        """
        Retrieves the farmer's PersonalizedContext and compiles it into a structured
        MemoryEvidence object. Returns None if consent is not granted or profile not found.
        """
        p_ctx: Optional[PersonalizationContext] = self.platform.get_personalized_context(farmer_id)
        if not p_ctx:
            logger.info(f"[AdaptiveRecommender] No personalization context loaded for: {farmer_id}")
            return None

        # Build patterns list
        patterns = []
        if p_ctx.twin.irrigation_type:
            patterns.append(f"irrigation:{p_ctx.twin.irrigation_type}")
        for crop_hist in p_ctx.twin.crop_history:
            crop_name = crop_hist.get("crop", "unknown")
            patterns.append(f"past_crop:{crop_name}")
        for disease in p_ctx.memory.diseases:
            d_name = disease.get("disease", "unknown")
            patterns.append(f"disease_history:{d_name}")
        for scheme in p_ctx.twin.scheme_history:
            patterns.append(f"scheme:{scheme}")

        # Construct explanation reasoning string for the ChiefReasoningAgent
        risk_posture = p_ctx.profile.risk_tolerance
        budget_avail = p_ctx.profile.budget_limit - p_ctx.profile.budget_spent
        summary_reasoning = (
            f"Farmer {p_ctx.profile.name} (experience={p_ctx.profile.experience_level}) "
            f"has a {risk_posture} risk tolerance and {budget_avail:.2f} INR remaining budget. "
            f"Farm located at {p_ctx.twin.village}, {p_ctx.twin.district}, {p_ctx.twin.state}. "
            f"Past goals: {', '.join(p_ctx.profile.farm_goals) or 'none'}. "
            f"Past crops yield: {', '.join([str(c.get('crop')) for c in p_ctx.twin.crop_history]) or 'none'}."
        )

        evidence = MemoryEvidence(
            id=f"EV-MEM-{uuid.uuid4().hex[:6].upper()}",
            source="PersonalizationPlatform",
            agent="AdaptiveRecommendationEngine",
            timestamp=time.time(),
            confidence=1.0,
            weight=1.2,  # high weight to ensure history matches are prioritized
            reasoning=summary_reasoning,
            farmer_id=farmer_id,
            historical_patterns=patterns,
            metadata={
                "risk_tolerance": risk_posture,
                "budget_limit": p_ctx.profile.budget_limit,
                "budget_spent": p_ctx.profile.budget_spent,
                "preferred_language": p_ctx.profile.preferred_language,
                "village": p_ctx.twin.village,
                "district": p_ctx.twin.district,
                "state": p_ctx.twin.state,
                "soil_ph": p_ctx.twin.soil_history[0].get("ph", 7.0) if p_ctx.twin.soil_history else 7.0,
                "irrigation_type": p_ctx.twin.irrigation_type,
            },
            ontology_references=[f"farmer_{farmer_id}"]
        )

        logger.info(f"[AdaptiveRecommender] Compiled MemoryEvidence for '{farmer_id}' with {len(patterns)} patterns.")
        return evidence
