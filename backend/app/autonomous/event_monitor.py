import logging
from typing import Any, Dict, List, cast

logger = logging.getLogger("kisan_mitra_ai.autonomous.event_monitor")

class EventMonitor:
    """
    Monitors data streams (weather, schemes, market, digital twin predictions)
    for anomalies, upcoming deadlines, or price changes.
    """
    def __init__(self, container: Any) -> None:
        self.container = container

    def monitor_weather(self, location: str) -> Dict[str, Any]:
        """
        Checks for weather updates and warnings.
        """
        try:
            weather_svc = self.container.weather_service
            forecast = weather_svc.get_forecast(location)
            warnings = forecast.get("warnings", [])
            return {
                "location": location,
                "warnings": warnings,
                "temperature": forecast.get("temperature", 30.0),
                "humidity": forecast.get("humidity", 60.0),
                "has_warning": len(warnings) > 0
            }
        except Exception as e:
            logger.warning(f"[EventMonitor] Weather monitor failed: {e}")
            return {"location": location, "warnings": [], "has_warning": False}

    def monitor_schemes(self) -> List[Dict[str, Any]]:
        """
        Checks for upcoming scheme application deadlines.
        """
        try:
            scheme_svc = self.container.scheme_service
            schemes = scheme_svc.get_active_schemes()
            upcoming_deadlines = []
            for s in schemes:
                deadline = s.get("deadline")
                if deadline:
                    upcoming_deadlines.append(s)
            return upcoming_deadlines
        except Exception as e:
            logger.warning(f"[EventMonitor] Schemes monitor failed: {e}")
            return []

    def monitor_market_prices(self, crop: str) -> Dict[str, Any]:
        """
        Monitors market prices for specific crop changes.
        """
        try:
            market_svc = self.container.market_service
            prices = market_svc.get_current_prices(crop)
            return {
                "crop": crop,
                "price": prices.get("average_price", 0.0),
                "trend": prices.get("trend", "stable"),
                "change_pct": prices.get("change_pct", 0.0)
            }
        except Exception as e:
            logger.warning(f"[EventMonitor] Market price monitor failed: {e}")
            return {"crop": crop, "price": 0.0, "trend": "stable", "change_pct": 0.0}

    def monitor_crop_advisories(self, crop: str, region: str) -> List[Dict[str, Any]]:
        """
        Monitors manuals and agronomy databases for regional advice changes.
        """
        try:
            knowledge_svc = self.container.knowledge_service
            docs = knowledge_svc.search(f"{crop} advisory in {region}")
            return cast(List[Dict[str, Any]], docs)
        except Exception as e:
            logger.warning(f"[EventMonitor] Advisories monitor failed: {e}")
            return []

    def monitor_digital_twin_forecasts(self, farmer_id: str) -> Dict[str, Any]:
        """
        Reads latest digital twin predictions and risks.
        """
        try:
            twin = self.container.twin_manager.get_twin(farmer_id)
            if twin:
                return {
                    "predictions": twin.predictions,
                    "risks": twin.risks,
                    "proactive_recs": twin.recommendations
                }
        except Exception as e:
            logger.warning(f"[EventMonitor] Twin monitor failed: {e}")
        return {"predictions": {}, "risks": {}, "proactive_recs": []}
