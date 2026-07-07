import logging
from typing import Any, Dict

from app.autonomous.alert_engine import AlertEngine
from app.autonomous.event_monitor import EventMonitor
from app.autonomous.notification_engine import NotificationEngine
from app.autonomous.priority_engine import PriorityEngine
from app.autonomous.reminder_engine import ReminderEngine
from app.autonomous.scheduler import Scheduler

logger = logging.getLogger("kisan_mitra_ai.autonomous.autonomous_manager")

class AutonomousManager:
    """
    Coordinator orchestration engine managing time scheduler loops, monitoring,
    event prioritization, and dispatch pipelines.
    """
    def __init__(self, container: Any, history_path: str = "./data/notification_history.json") -> None:
        self.container = container
        self.scheduler = Scheduler()
        self.event_monitor = EventMonitor(container)
        self.reminder_engine = ReminderEngine(container)
        self.alert_engine = AlertEngine(container)
        self.notification_engine = NotificationEngine(container, history_path)

        self.setup_schedules()

    def setup_schedules(self) -> None:
        # Register default daily monitoring cycle
        self.scheduler.register_job(
            name="daily_farmer_monitoring",
            schedule_type="daily",
            callback=self.run_daily_monitoring
        )

    def run_daily_monitoring(self, *args: Any, **kwargs: Any) -> None:
        logger.info("[AutonomousManager] Commencing daily monitoring cycle...")
        p_platform = self.container.personalization_platform
        for farmer_id in list(p_platform.profiles.keys()):
            self.run_monitoring_cycle(farmer_id)

    def calculate_priority_score(self, due_date: float, urgency_factor: float, impact_factor: float) -> str:
        return PriorityEngine.calculate_priority(due_date, urgency_factor, impact_factor)

    def run_monitoring_cycle(self, farmer_id: str) -> Dict[str, Any]:
        """
        Executes monitoring pipelines, evaluates alerts and reminders,
        applies urgency priority mappings, and dispatches notifications.
        """
        logger.info(f"[AutonomousManager] Running monitoring cycle for '{farmer_id}'...")

        # 1. Monitor forecasts and digital twin
        twin_state = self.event_monitor.monitor_digital_twin_forecasts(farmer_id)

        district = twin_state.get("twin", {}).get("district", "Ludhiana")
        next_crop = twin_state.get("predictions", {}).get("next_crop", "Wheat")

        weather_info = self.event_monitor.monitor_weather(district)
        market_info = self.event_monitor.monitor_market_prices(next_crop)

        # 2. Run engines
        reminders = self.reminder_engine.generate_reminders(farmer_id, twin_state)
        alerts = self.alert_engine.generate_alerts(farmer_id, twin_state, weather_info, market_info)

        all_actions = reminders + alerts
        dispatched_logs = []

        # 3. Prioritize & Queue Notifications
        for item in all_actions:
            # Default impact mapping
            impact = 5.0
            if "CRITICAL WEATHER" in item.message:
                impact = 9.0
            elif "DISEASE WARNING" in item.message:
                impact = 8.0
            elif "WATER SHORTAGE" in item.message:
                impact = 7.5
            elif "MARKET OPPORTUNITY" in item.message:
                impact = 6.0

            priority_class = self.calculate_priority_score(item.due_date, 0.0, impact)
            item.priority = priority_class

            # Dispatch notification
            log = self.notification_engine.dispatch_notification(farmer_id, item)
            dispatched_logs.append(log)

        return {
            "farmer_id": farmer_id,
            "reminders_count": len(reminders),
            "alerts_count": len(alerts),
            "dispatched": dispatched_logs
        }
