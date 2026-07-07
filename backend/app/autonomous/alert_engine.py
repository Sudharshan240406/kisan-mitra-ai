import logging
import time
from typing import Any, List

from app.personalization.models import Reminder

logger = logging.getLogger("kisan_mitra_ai.autonomous.alert_engine")

class AlertEngine:
    """
    Generates hazard alerts based on weather warnings, high disease probability,
    financial overruns, water deficits, and crop price fluctuations.
    """
    def __init__(self, container: Any) -> None:
        self.container = container

    def generate_alerts(self, farmer_id: str, twin_state: dict[str, Any], weather_info: dict[str, Any], market_info: dict[str, Any]) -> List[Reminder]:
        alerts: List[Reminder] = []
        p_platform = self.container.personalization_platform
        scheduler_svc = p_platform.registry.get("reminder_scheduler")

        # 1. Weather risks
        if weather_info.get("has_warning"):
            for warning in weather_info.get("warnings", []):
                alerts.append(Reminder(
                    farmer_id=farmer_id,
                    type="weather_alert",
                    message=f"CRITICAL WEATHER WARNING: {warning} forecast for {weather_info.get('location')}.",
                    due_date=time.time() + 86400.0,
                    priority="high"
                ))

        # 2. Disease risks
        disease_prob = twin_state.get("predictions", {}).get("disease_probability", {})
        prob_val = disease_prob.get("probability", 0.0)
        disease_name = disease_prob.get("disease", "pathogen")
        if prob_val >= 0.30:
            alerts.append(Reminder(
                farmer_id=farmer_id,
                type="disease_monitoring",
                message=f"DISEASE WARNING: Elevated probability ({prob_val*100:.0f}%) of {disease_name} infection detected.",
                due_date=time.time() + 3 * 86400.0,
                priority="high"
            ))

        # 3. Water shortages
        water_demand = twin_state.get("predictions", {}).get("water_demand_liters", 0.0)
        irrigation_type = twin_state.get("twin", {}).get("irrigation_type", "rainfed")
        weather_risk = twin_state.get("risks", {}).get("weather_risk", 0.0)
        if weather_risk >= 0.50 and irrigation_type == "rainfed" and water_demand > 500000.0:
            alerts.append(Reminder(
                farmer_id=farmer_id,
                type="irrigation",
                message="WATER SHORTAGE ALERT: High weather risk combined with rainfed irrigation limits water availability. Consider efficient drip options.",
                due_date=time.time() + 2 * 86400.0,
                priority="high"
            ))

        # 4. Market opportunities
        trend = market_info.get("trend", "stable")
        change_pct = market_info.get("change_pct", 0.0)
        crop = market_info.get("crop", "crop")
        if trend == "bullish" or change_pct >= 10.0:
            alerts.append(Reminder(
                farmer_id=farmer_id,
                type="market_alert",
                message=f"MARKET OPPORTUNITY: Spot market prices for {crop} surged by {change_pct:.1f}%. Consider selling surplus stock.",
                due_date=time.time() + 2 * 86400.0,
                priority="medium"
            ))

        # 5. Financial risks
        budget_spent = twin_state.get("profile", {}).get("budget_spent", 0.0)
        budget_limit = twin_state.get("profile", {}).get("budget_limit", 1.0)
        spent_ratio = budget_spent / max(budget_limit, 1.0)
        crop_failure_risk = twin_state.get("risks", {}).get("crop_failure_risk", 0.0)

        if spent_ratio >= 0.80 or crop_failure_risk >= 0.50:
            alerts.append(Reminder(
                farmer_id=farmer_id,
                type="market_alert",
                message=f"FINANCIAL RISK THREAT: Seasonal budget capacity spent is at {spent_ratio*100:.0f}%, with a crop failure risk index of {crop_failure_risk*100:.0f}%.",
                due_date=time.time() + 4 * 86400.0,
                priority="high"
            ))

        # Save to scheduler service
        for alert in alerts:
            try:
                scheduler_svc.schedule_reminder(alert)
            except Exception as e:
                logger.warning(f"[AlertEngine] Failed to schedule alert: {e}")

        return alerts
