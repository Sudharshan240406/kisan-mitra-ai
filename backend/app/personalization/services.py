"""
Kisan Mitra AI — Personalization Services
=========================================
Implements the core domain services for profile updates, digital twin tracking,
long-term memories ingestion, reminder scheduling, continuous learning loops,
and privacy consent management.
"""
from __future__ import annotations

import logging
import time
from typing import Any, List, Optional

from app.personalization.models import (
    FarmDetails,
    FarmerProfile,
    LongTermMemory,
    PrivacyConsent,
    Reminder,
)
from app.personalization.platform import PersonalizationPlatform

logger = logging.getLogger("kisan_mitra_ai.personalization.services")


class ProfileManagerService:
    """
    Service responsible for editing and fetching farmer profiles and language choices.
    """
    def __init__(self, platform: PersonalizationPlatform) -> None:
        self.platform = platform

    def get_profile(self, farmer_id: str) -> Optional[FarmerProfile]:
        return self.platform.profiles.get(farmer_id)

    def create_or_update_profile(self, profile: FarmerProfile) -> FarmerProfile:
        farmer_id = profile.farmer_id
        is_new = farmer_id not in self.platform.profiles
        self.platform.profiles[farmer_id] = profile

        if farmer_id not in self.platform.twins:
            self.platform.twins[farmer_id] = FarmDetails(
                farmer_id=farmer_id, land_size_acres=0.0, village="unknown", district="unknown", state="unknown"
            )
        if farmer_id not in self.platform.memories:
            self.platform.memories[farmer_id] = LongTermMemory(farmer_id=farmer_id)
        if farmer_id not in self.platform.consents:
            self.platform.consents[farmer_id] = PrivacyConsent(farmer_id=farmer_id)
        if farmer_id not in self.platform.reminders:
            self.platform.reminders[farmer_id] = []

        logger.info(f"[ProfileManagerService] Saved profile for farmer: {farmer_id}")
        self.platform.save_to_disk()
        return profile


class DigitalTwinService:
    """
    Service responsible for updating and synchronizing physical farm features,
    irrigation options, crop lists, and soil testing logs.
    """
    def __init__(self, platform: PersonalizationPlatform) -> None:
        self.platform = platform

    def get_twin(self, farmer_id: str) -> Optional[FarmDetails]:
        return self.platform.twins.get(farmer_id)

    def update_twin(self, twin: FarmDetails) -> FarmDetails:
        self.platform.twins[twin.farmer_id] = twin
        logger.info(f"[DigitalTwinService] Updated digital twin details for: {twin.farmer_id}")
        self.platform.save_to_disk()
        return twin

    def add_soil_record(self, farmer_id: str, record: dict[str, Any]) -> Optional[FarmDetails]:
        twin = self.get_twin(farmer_id)
        if twin:
            record.setdefault("tested_at", time.time())
            twin.soil_history.append(record)
            logger.info(f"[DigitalTwinService] Appended soil health record for: {farmer_id}")
            self.platform.save_to_disk()
        return twin

    def add_crop_record(self, farmer_id: str, record: dict[str, Any]) -> Optional[FarmDetails]:
        twin = self.get_twin(farmer_id)
        if twin:
            twin.crop_history.append(record)
            logger.info(f"[DigitalTwinService] Appended crop history record for: {farmer_id}")
            self.platform.save_to_disk()
        return twin


class LongTermMemoryService:
    """
    Service tracking conversation logs, issued advisories, weather/disease anomalies,
    and outcome results over time.
    """
    def __init__(self, platform: PersonalizationPlatform) -> None:
        self.platform = platform

    def get_memory(self, farmer_id: str) -> LongTermMemory:
        if farmer_id not in self.platform.memories:
            self.platform.memories[farmer_id] = LongTermMemory(farmer_id=farmer_id)
        return self.platform.memories[farmer_id]

    def log_conversation(self, farmer_id: str, query: str, response: str) -> None:
        memory = self.get_memory(farmer_id)
        if memory:
            memory.conversations.append({
                "timestamp": time.time(),
                "query": query,
                "response": response
            })
            # keep conversation history bounded to 50 items
            if len(memory.conversations) > 50:
                memory.conversations.pop(0)
            self.platform.save_to_disk()

    def log_recommendation(self, farmer_id: str, rec_id: str, text: str, confidence: float) -> None:
        memory = self.get_memory(farmer_id)
        if memory:
            memory.recommendations.append({
                "recommendation_id": rec_id,
                "text": text,
                "feedback": None,
                "timestamp": time.time(),
            })
            memory.ai_confidence_history.append(confidence)
            self.platform.metrics.memory_usage_records = sum(
                len(m.conversations) + len(m.recommendations) for m in self.platform.memories.values()
            )
            self.platform.save_to_disk()

    def log_feedback(self, farmer_id: str, rec_id: str, rating: int, comment: str = "") -> None:
        memory = self.get_memory(farmer_id)
        if memory:
            # Update recommendation feedback
            for rec in memory.recommendations:
                if rec.get("recommendation_id") == rec_id:
                    rec["feedback"] = "good" if rating >= 4 else "bad"

            # Save in feedback history list
            memory.feedback_history.append({
                "recommendation_id": rec_id,
                "score": rating,
                "comment": comment,
                "timestamp": time.time()
            })
            logger.info(f"[LongTermMemoryService] Logged feedback for recommendation {rec_id} (rating={rating})")
            self.platform.save_to_disk()


class ReminderSchedulerService:
    """
    Service coordinating agricultural calendar reminders, deadlines, and notifications.
    """
    def __init__(self, platform: PersonalizationPlatform) -> None:
        self.platform = platform

    def get_reminders(
        self, farmer_id: str, status_filter: Optional[str] = None, status: Optional[str] = None
    ) -> List[Reminder]:
        reminders = self.platform.reminders.get(farmer_id, [])
        target_status = status_filter or status
        if target_status:
            return [r for r in reminders if r.status == target_status]
        return reminders

    def schedule_reminder(self, reminder: Reminder) -> Reminder:
        fid = reminder.farmer_id
        if fid not in self.platform.reminders:
            self.platform.reminders[fid] = []
        self.platform.reminders[fid].append(reminder)
        self._update_reminder_metrics()
        logger.info(f"[ReminderSchedulerService] Scheduled reminder '{reminder.reminder_id}' for {fid}")
        self.platform.save_to_disk()
        return reminder

    def dismiss_reminder(self, farmer_id: str, reminder_id: str) -> bool:
        reminders = self.platform.reminders.get(farmer_id, [])
        for r in reminders:
            if r.reminder_id == reminder_id:
                r.status = "dismissed"
                self._update_reminder_metrics()
                logger.info(f"[ReminderSchedulerService] Dismissed reminder '{reminder_id}'")
                self.platform.save_to_disk()
                return True
        return False

    def mark_sent(self, farmer_id: str, reminder_id: str) -> bool:
        reminders = self.platform.reminders.get(farmer_id, [])
        for r in reminders:
            if r.reminder_id == reminder_id:
                r.status = "sent"
                self._update_reminder_metrics()
                logger.info(f"[ReminderSchedulerService] Marked reminder '{reminder_id}' as sent")
                self.platform.save_to_disk()
                return True
        return False

    def _update_reminder_metrics(self) -> None:
        all_reminders = []
        for rl in self.platform.reminders.values():
            all_reminders.extend(rl)
        self.platform.metrics.reminders_pending = sum(1 for r in all_reminders if r.status == "pending")
        self.platform.metrics.reminders_delivered = sum(1 for r in all_reminders if r.status == "sent")


class ContinuousLearningService:
    """
    Analyzes logged outcomes and ratings to adjust farmer preferences and profile risk levels.
    """
    def __init__(self, platform: PersonalizationPlatform) -> None:
        self.platform = platform

    def run_learning_iteration(self, farmer_id: str) -> dict[str, Any]:
        """
        Processes feedback history for a farmer, adapts risk tolerance or budget adjustments
        if consistent success/failure patterns emerge, and increments iteration counts.
        """
        profile = self.platform.profiles.get(farmer_id)
        if not profile:
            return {"status": "error", "message": "Farmer profile missing."}
        memory = self.platform.memories.get(farmer_id)
        if not memory:
            memory = LongTermMemory(farmer_id=farmer_id)
            self.platform.memories[farmer_id] = memory

        self.platform.metrics.learning_iterations += 1

        feedbacks = memory.feedback_history
        if not feedbacks:
            return {"status": "noop", "message": "No new feedback items to process."}

        avg_score = sum(fb["score"] for fb in feedbacks) / len(feedbacks)
        acceptance = sum(1 for fb in feedbacks if fb["score"] >= 4)
        rejection = len(feedbacks) - acceptance

        self.platform.metrics.recommendation_acceptance_count += acceptance
        self.platform.metrics.recommendation_rejections += rejection

        # Adjust personalization accuracy dynamically
        total_fb = len(feedbacks)
        self.platform.metrics.accuracy_score = (acceptance / total_fb) if total_fb > 0 else 1.0

        # Learning Rule 1: High success rates lead to potentially higher budget caps or progressive goals
        if avg_score >= 4.5 and len(feedbacks) >= 2:
            if profile.risk_tolerance == "low":
                profile.risk_tolerance = "medium"
                logger.info(f"[ContinuousLearning] Upgraded risk tolerance of '{farmer_id}' to 'medium' due to positive outcome trends.")
            profile.budget_limit = float(profile.budget_limit * 1.1)

        # Learning Rule 2: Low scores trigger risk tolerance mitigation down to 'low'
        elif avg_score < 3.0 and len(feedbacks) >= 2:
            if profile.risk_tolerance in ("medium", "high"):
                profile.risk_tolerance = "low"
                logger.info(f"[ContinuousLearning] Downgraded risk tolerance of '{farmer_id}' to 'low' due to low rating alerts.")

        self.platform.save_to_disk()
        return {
            "status": "success",
            "feedback_processed": len(feedbacks),
            "avg_score": round(avg_score, 2),
            "new_risk_tolerance": profile.risk_tolerance,
            "new_budget_limit": round(profile.budget_limit, 2),
        }


class PrivacyConsentService:
    """
    Manages privacy preferences, consent, and scrubs/deletes farmer data upon request.
    """
    def __init__(self, platform: PersonalizationPlatform) -> None:
        self.platform = platform

    def get_consent(self, farmer_id: str) -> Optional[PrivacyConsent]:
        return self.platform.consents.get(farmer_id)

    def update_consent(self, consent: PrivacyConsent) -> PrivacyConsent:
        self.platform.consents[consent.farmer_id] = consent
        logger.info(f"[PrivacyConsentService] Updated privacy consent settings for: {consent.farmer_id}")
        self.platform.save_to_disk()
        return consent

    def scrub_farmer_memory(self, farmer_id: str) -> bool:
        """
        Deletes all conversation histories, recommendations, and feedback for privacy compliance (Right to be Forgotten).
        """
        memory = self.platform.memories.get(farmer_id)
        if memory:
            memory.conversations.clear()
            memory.recommendations.clear()
            memory.feedback_history.clear()
            memory.diseases.clear()
            memory.weather_events.clear()
            memory.market_decisions.clear()
            memory.historical_outcomes.clear()
            memory.ai_confidence_history.clear()

            # clear active reminders
            if farmer_id in self.platform.reminders:
                self.platform.reminders[farmer_id].clear()

            logger.info(f"[PrivacyConsentService] Scrubbed all personalization memories and alerts for farmer: {farmer_id}")
            self.platform.save_to_disk()
            return True
        return False
