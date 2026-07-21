"""
Kisan Mitra AI — Personalization Platform
=========================================
Implements the central Personalization Platform hub, registries, in-memory data
stores, metrics tracking, and context assemblers.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from app.personalization.models import (
    FarmDetails,
    FarmerProfile,
    LongTermMemory,
    PersonalizationContext,
    PrivacyConsent,
    Reminder,
)
from pydantic import BaseModel

logger = logging.getLogger("kisan_mitra_ai.personalization.platform")


class PersonalizationMetrics(BaseModel):
    """
    Performance and accuracy metrics tracker for personalization.
    """
    total_profiles: int = 0
    memory_usage_records: int = 0
    reminders_delivered: int = 0
    reminders_pending: int = 0
    recommendation_acceptance_count: int = 0
    recommendation_rejections: int = 0
    learning_iterations: int = 0
    accuracy_score: float = 1.0  # mock metric: rating of personalization success

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_profiles": self.total_profiles,
            "memory_usage_records": self.memory_usage_records,
            "reminders_delivered": self.reminders_delivered,
            "reminders_pending": self.reminders_pending,
            "recommendation_acceptance_count": self.recommendation_acceptance_count,
            "recommendation_rejections": self.recommendation_rejections,
            "learning_iterations": self.learning_iterations,
            "accuracy_score": round(self.accuracy_score, 2),
        }


class PersonalizationRegistry:
    """
    Enables pluggable service registration for components of the personalization engine.
    """
    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}

    def register(self, name: str, service: Any) -> None:
        self._services[name] = service
        logger.info(f"[PersonalizationRegistry] Registered service: '{name}'")

    def get(self, name: str) -> Any:
        service = self._services.get(name)
        if service is None:
            raise KeyError(f"[PersonalizationRegistry] Service '{name}' not found.")
        return service

    def list_services(self) -> List[str]:
        return list(self._services.keys())


class PersonalizationPlatform:
    """
    Central orchestrator for Personalized Farmer AI. Stores profiles, digital
    twin details, long-term memory logs, reminders, and consent preferences.
    """
    def __init__(self) -> None:
        self.registry = PersonalizationRegistry()
        self.metrics = PersonalizationMetrics()

        # In-memory storage structures acting as DB
        self.profiles: Dict[str, FarmerProfile] = {}
        self.twins: Dict[str, FarmDetails] = {}
        self.memories: Dict[str, LongTermMemory] = {}
        self.consents: Dict[str, PrivacyConsent] = {}
        self.reminders: Dict[str, List[Reminder]] = {}

        if not self.load_from_disk():
            self._prepopulate_default_farmers()
            self.save_to_disk()
        logger.info("[PersonalizationPlatform] Personalized Farmer AI platform initialized.")

    def save_to_disk(self) -> None:
        """Saves current personalization state to local JSON files under data/farmers/."""
        import json
        import os
        try:
            os.makedirs("data/farmers", exist_ok=True)
            with open("data/farmers/profiles.json", "w", encoding="utf-8") as f:
                json.dump({k: v.model_dump() for k, v in self.profiles.items()}, f, ensure_ascii=False, indent=2)
            with open("data/farmers/twins.json", "w", encoding="utf-8") as f:
                json.dump({k: v.model_dump() for k, v in self.twins.items()}, f, ensure_ascii=False, indent=2)
            with open("data/farmers/memories.json", "w", encoding="utf-8") as f:
                json.dump({k: v.model_dump() for k, v in self.memories.items()}, f, ensure_ascii=False, indent=2)
            with open("data/farmers/consents.json", "w", encoding="utf-8") as f:
                json.dump({k: v.model_dump() for k, v in self.consents.items()}, f, ensure_ascii=False, indent=2)

            reminders_dict = {}
            for k, val_list in self.reminders.items():
                reminders_dict[k] = [r.model_dump() for r in val_list]
            with open("data/farmers/reminders.json", "w", encoding="utf-8") as f:
                json.dump(reminders_dict, f, ensure_ascii=False, indent=2)
            logger.debug("[PersonalizationPlatform] Saved state to local files.")
        except Exception as e:
            logger.error(f"[PersonalizationPlatform] Failed to save state to disk: {e}")

    def load_from_disk(self) -> bool:
        """Loads state from local JSON files under data/farmers/. Returns True if successfully loaded."""
        import json
        import os
        if not os.path.exists("data/farmers/profiles.json"):
            return False
        try:
            with open("data/farmers/profiles.json", "r", encoding="utf-8") as f:
                self.profiles = {k: FarmerProfile(**v) for k, v in json.load(f).items()}
            if os.path.exists("data/farmers/twins.json"):
                with open("data/farmers/twins.json", "r", encoding="utf-8") as f:
                    self.twins = {k: FarmDetails(**v) for k, v in json.load(f).items()}
            if os.path.exists("data/farmers/memories.json"):
                with open("data/farmers/memories.json", "r", encoding="utf-8") as f:
                    self.memories = {k: LongTermMemory(**v) for k, v in json.load(f).items()}
            if os.path.exists("data/farmers/consents.json"):
                with open("data/farmers/consents.json", "r", encoding="utf-8") as f:
                    self.consents = {k: PrivacyConsent(**v) for k, v in json.load(f).items()}
            if os.path.exists("data/farmers/reminders.json"):
                with open("data/farmers/reminders.json", "r", encoding="utf-8") as f:
                    self.reminders = {k: [Reminder(**r) for r in v] for k, v in json.load(f).items()}
            self.metrics.total_profiles = len(self.profiles)
            logger.info(f"[PersonalizationPlatform] Successfully loaded {len(self.profiles)} profiles from disk.")
            return True
        except Exception as e:
            logger.error(f"[PersonalizationPlatform] Error loading state from disk: {e}")
            return False

    def _prepopulate_default_farmers(self) -> None:
        """Pre-populates Ramesh Singh and Siddappa Gowda to mirror knowledge graph."""
        # 1. Ramesh Singh
        ramesh_id = "farmer_ramesh"
        self.profiles[ramesh_id] = FarmerProfile(
            farmer_id=ramesh_id,
            name="Ramesh Singh",
            preferred_language="hi",
            experience_level="intermediate",
            risk_tolerance="medium",
            budget_limit=150000.0,
            budget_spent=45000.0,
            farm_goals=["Maximize wheat yield", "Install drip irrigation"],
        )
        self.twins[ramesh_id] = FarmDetails(
            farmer_id=ramesh_id,
            land_size_acres=5.0,
            village="Kila Raipur",
            district="Ludhiana",
            state="Punjab",
            climate_zone="Trans-Gangetic Plains",
            crop_zone="Wheat-Rice Zone",
            crop_history=[
                {"crop": "wheat", "season": "Rabi", "year": 2025, "yield_tonnes": 5.2},
                {"crop": "rice", "season": "Kharif", "year": 2025, "yield_tonnes": 4.8},
            ],
            soil_history=[
                {"ph": 6.8, "nitrogen": "medium", "phosphorus": "medium", "potassium": "high", "tested_at": time.time() - 30 * 86400}
            ],
            equipment=["Tractor", "Seed Drill"],
            livestock=["Cows (2)"],
            irrigation_type="tube_well",
            scheme_history=["PM-Kisan", "PMFBY"],
        )
        self.memories[ramesh_id] = LongTermMemory(
            farmer_id=ramesh_id,
            conversations=[
                {"timestamp": time.time() - 5000, "query": "When should I sow wheat?", "response": "Sow wheat during mid-November."}
            ],
            recommendations=[
                {"recommendation_id": "REC-RAM-01", "text": "Apply Urea fertilizer in wheat crop", "feedback": "good", "timestamp": time.time() - 10000}
            ],
            diseases=[{"disease": "Yellow Rust", "date": "2025-02-10"}],
            weather_events=[{"event": "Delayed Monsoon", "date": "2025-07-01"}],
            market_decisions=[{"commodity": "wheat", "price": 2275.0, "mandi": "Ludhiana Mandi", "date": "2025-05-15"}],
            feedback_history=[{"recommendation_id": "REC-RAM-01", "score": 5, "comment": "Wheat crop yields increased by 10%!"}],
            ai_confidence_history=[0.85, 0.90],
            historical_outcomes=[{"year": 2025, "net_profit_inr": 85000.0}],
        )
        self.consents[ramesh_id] = PrivacyConsent(farmer_id=ramesh_id, consent_given=True)
        self.reminders[ramesh_id] = [
            Reminder(
                farmer_id=ramesh_id,
                type="fertilizer",
                message="Time to apply second dose of Nitrogen fertilizer on Wheat crop.",
                due_date=time.time() + 86400 * 3,
                priority="high",
            )
        ]

        # 2. Siddappa Gowda
        siddappa_id = "farmer_siddappa"
        self.profiles[siddappa_id] = FarmerProfile(
            farmer_id=siddappa_id,
            name="Siddappa Gowda",
            preferred_language="kn",
            experience_level="expert",
            risk_tolerance="low",
            budget_limit=120000.0,
            budget_spent=60000.0,
            farm_goals=["Optimize rice irrigation", "Organic soil conditioning"],
        )
        self.twins[siddappa_id] = FarmDetails(
            farmer_id=siddappa_id,
            land_size_acres=3.5,
            village="Heggeri",
            district="Dharwad",
            state="Karnataka",
            climate_zone="Southern Plateau and Hills",
            crop_zone="Rice Zone",
            crop_history=[
                {"crop": "rice", "season": "Kharif", "year": 2025, "yield_tonnes": 4.1}
            ],
            soil_history=[
                {"ph": 6.2, "nitrogen": "low", "phosphorus": "high", "potassium": "medium", "tested_at": time.time() - 60 * 86400}
            ],
            equipment=["Power Tiller"],
            livestock=["Buffaloes (3)"],
            irrigation_type="canal",
            scheme_history=["PM-Kisan"],
        )
        self.memories[siddappa_id] = LongTermMemory(
            farmer_id=siddappa_id,
            conversations=[
                {"timestamp": time.time() - 8000, "query": "What fertilizer is best for rice?", "response": "NPK 15:15:15 complex fertilizer."}
            ],
            recommendations=[
                {"recommendation_id": "REC-SID-01", "text": "Apply Zinc sulphate to rice crop", "feedback": "good", "timestamp": time.time() - 15000}
            ],
            diseases=[{"disease": "Rice Blast", "date": "2025-09-05"}],
            weather_events=[{"event": "Dry Spell", "date": "2025-08-12"}],
            market_decisions=[{"commodity": "rice", "price": 2100.0, "mandi": "Dharwad Mandi", "date": "2025-10-01"}],
            feedback_history=[{"recommendation_id": "REC-SID-01", "score": 4, "comment": "Yellowing of leaves stopped after Zinc application"}],
            ai_confidence_history=[0.82, 0.88],
            historical_outcomes=[{"year": 2025, "net_profit_inr": 62000.0}],
        )
        self.consents[siddappa_id] = PrivacyConsent(farmer_id=siddappa_id, consent_given=True)
        self.reminders[siddappa_id] = [
            Reminder(
                farmer_id=siddappa_id,
                type="irrigation",
                message="Check canal water release timing and irrigate rice field.",
                due_date=time.time() + 86400 * 2,
                priority="medium",
            )
        ]

        self.metrics.total_profiles = 2
        self.metrics.memory_usage_records = 2
        self.metrics.reminders_pending = 2

    def get_personalized_context(self, farmer_id: str) -> Optional[PersonalizationContext]:
        """
        Retrieves consolidated PersonalizationContext for a farmer.
        Checks privacy consent. If personalization consent is revoked, returns None.
        """
        consent = self.consents.get(farmer_id)
        if not consent or not consent.consent_given:
            logger.info(f"[PersonalizationPlatform] Personalization blocked or consent not given for: {farmer_id}")
            return None

        profile = self.profiles.get(farmer_id)
        twin = self.twins.get(farmer_id)
        memory = self.memories.get(farmer_id)
        reminders = self.reminders.get(farmer_id, [])

        if not profile or not twin or not memory:
            logger.warning(f"[PersonalizationPlatform] Context missing complete profile/twin/memory for: {farmer_id}")
            return None

        return PersonalizationContext(
            farmer_id=farmer_id,
            profile=profile,
            twin=twin,
            memory=memory,
            consent=consent,
            reminders=reminders,
        )

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "registered_services": self.registry.list_services(),
            "metrics": self.metrics.to_dict(),
        }
