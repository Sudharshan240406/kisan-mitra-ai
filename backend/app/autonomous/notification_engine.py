import json
import logging
import os
import time
from typing import Any, Dict, List

from app.personalization.models import Reminder

logger = logging.getLogger("kisan_mitra_ai.autonomous.notification_engine")

class NotificationEngine:
    """
    Constructs and dispatches payload templates for SMS, Voice, Dashboard,
    and Push channels. Manages local delivery logs database.
    """
    def __init__(self, container: Any, history_path: str = "./data/notification_history.json") -> None:
        self.container = container
        self.history_path = history_path
        self.history: List[Dict[str, Any]] = []
        self.load_history()

    def load_history(self) -> None:
        if not os.path.exists(self.history_path):
            return
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except Exception as e:
            logger.error(f"[NotificationEngine] Failed to load notification history: {e}")

    def save_history(self) -> None:
        try:
            dir_name = os.path.dirname(self.history_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[NotificationEngine] Failed to save notification history: {e}")

    def dispatch_notification(self, farmer_id: str, reminder: Reminder) -> Dict[str, Any]:
        """
        Builds templates for all 4 notification channels and logs dispatch action.
        """
        start_time = time.time()
        # SMS payload
        sms_payload = {
            "to": farmer_id,
            "body": f"Kisan Mitra Alert: {reminder.message} Due: {time.strftime('%Y-%m-%d', time.localtime(reminder.due_date))}"
        }

        # Voice payload
        voice_payload = {
            "to": farmer_id,
            "tts_text": reminder.message,
            "play_welcome": True
        }

        # Dashboard payload
        dashboard_payload = {
            "farmer_id": farmer_id,
            "reminder_id": reminder.reminder_id,
            "type": reminder.type,
            "message": reminder.message,
            "due_date": reminder.due_date,
            "priority": reminder.priority,
            "status": reminder.status
        }

        # Mobile Push payload
        push_payload = {
            "device_token": f"token-{farmer_id}",
            "title": f"New Agricultural {reminder.priority.capitalize()} Event",
            "body": reminder.message,
            "data": {
                "reminder_id": reminder.reminder_id,
                "type": reminder.type
            }
        }

        dispatch_log = {
            "notification_id": f"NOTIF-{reminder.reminder_id}",
            "farmer_id": farmer_id,
            "timestamp": time.time(),
            "priority": reminder.priority,
            "sms": sms_payload,
            "voice": voice_payload,
            "dashboard": dashboard_payload,
            "push": push_payload,
            "status": "delivered"
        }

        self.history.append(dispatch_log)
        self.save_history()

        # Try SMS adapter dispatch
        try:
            sms_provider = self.container.sms_provider
            sms_provider.send_sms("+919999999999", sms_payload["body"])
        except Exception as e:
            logger.debug(f"[NotificationEngine] SMS dispatch skipped/failed: {e}")

        latency_ms = (time.time() - start_time) * 1000.0
        obs_mgr = getattr(self.container, "observability_manager", None)
        if obs_mgr:
            obs_mgr.metrics_engine.record("notification_latency", latency_ms)

        logger.info(f"[NotificationEngine] Dispatched priority '{reminder.priority}' notification {reminder.reminder_id}")
        return dispatch_log
