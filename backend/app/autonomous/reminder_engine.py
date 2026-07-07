import logging
import time
from typing import Any, List

from app.personalization.models import Reminder

logger = logging.getLogger("kisan_mitra_ai.autonomous.reminder_engine")

class ReminderEngine:
    """
    Generates structured reminders based on crop calendars, deadlines, and missing documents.
    """
    def __init__(self, container: Any) -> None:
        self.container = container

    def generate_reminders(self, farmer_id: str, twin_state: dict[str, Any]) -> List[Reminder]:
        reminders: List[Reminder] = []
        p_platform = self.container.personalization_platform
        scheduler_svc = p_platform.registry.get("reminder_scheduler")

        # 1. Scheme applications
        eligible_schemes = twin_state.get("predictions", {}).get("scheme_eligibility_changes", {}).get("eligible_new_schemes", [])
        for scheme in eligible_schemes:
            reminders.append(Reminder(
                farmer_id=farmer_id,
                type="scheme_deadline",
                message=f"Application deadline approaching for eligible scheme: {scheme}. Submit documents to enroll.",
                due_date=time.time() + 7 * 86400.0,
                priority="high"
            ))

        # 2. Insurance renewals
        next_crop = twin_state.get("predictions", {}).get("next_crop")
        if next_crop:
            reminders.append(Reminder(
                farmer_id=farmer_id,
                type="scheme_deadline",
                message=f"Agricultural insurance renewal deadline approaching for upcoming crop season: {next_crop}.",
                due_date=time.time() + 14 * 86400.0,
                priority="medium"
            ))

        # 3. Document submissions
        memory = p_platform.memories.get(farmer_id)
        if memory and hasattr(memory, "conversations"):
            for conv in memory.conversations[-3:]:
                resp = str(conv.get("response", "")).lower()
                if "submit" in resp or "upload" in resp or "document" in resp:
                    reminders.append(Reminder(
                        farmer_id=farmer_id,
                        type="disease_monitoring",
                        message="Reminder to submit the requested verification documents for active scheme processing.",
                        due_date=time.time() + 3 * 86400.0,
                        priority="high"
                    ))
                    break

        # 4. Crop activities (irrigation, sowing)
        water_demand = twin_state.get("predictions", {}).get("water_demand_liters", 0.0)
        irrigation_type = twin_state.get("twin", {}).get("irrigation_type", "rainfed")
        if water_demand > 1000000.0 and irrigation_type == "rainfed":
            reminders.append(Reminder(
                farmer_id=farmer_id,
                type="irrigation",
                message=f"Critical irrigation required for predicted next season crops. High water demand of {water_demand:.0f}L forecast.",
                due_date=time.time() + 2 * 86400.0,
                priority="high"
            ))

        if next_crop:
            reminders.append(Reminder(
                farmer_id=farmer_id,
                type="sowing",
                message=f"Prepare field for next crop season cycle. Recommended next crop: {next_crop}.",
                due_date=time.time() + 5 * 86400.0,
                priority="medium"
            ))

        # Save generated reminders to personalization registry
        for rem in reminders:
            try:
                scheduler_svc.schedule_reminder(rem)
            except Exception as e:
                logger.warning(f"[ReminderEngine] Failed to schedule reminder: {e}")

        return reminders
