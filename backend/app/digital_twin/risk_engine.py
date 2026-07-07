import logging
from typing import Any, Dict

logger = logging.getLogger("kisan_mitra_ai.digital_twin.risk_engine")

class RiskEngine:
    """
    Evaluates agricultural operational risk parameters driven by digital twin data states.
    """
    def calculate_risks(self, state: Dict[str, Any], predictions: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Weather risk evaluation (based on climate classification)
        climate = str(state.get("climate_zone", "")).strip().lower()
        weather_risk = 0.20
        if "semi-arid" in climate:
            weather_risk = 0.50
        elif "arid" in climate or "dry" in climate:
            weather_risk = 0.70
        elif "humid" in climate:
            weather_risk = 0.30

        # 2. Crop failure risk estimation (based on water source vulnerability)
        irrigation = state.get("irrigation_type", "rainfed")
        crop_failure_risk = weather_risk * 0.8

        if irrigation == "rainfed":
            crop_failure_risk += 0.25
        elif irrigation in ["drip", "sprinkler"]:
            crop_failure_risk -= 0.15

        crop_failure_risk = float(max(0.05, min(0.95, crop_failure_risk)))

        # 3. Disease risk mapping (based on prediction engine outcomes)
        disease_prob = predictions.get("disease_probability", {}).get("probability", 0.15)
        disease_risk = float(disease_prob)

        # 4. Financial risk tracking (based on spent budgets and farmer experiences)
        spent = float(state.get("budget_spent", 0.0))
        limit = float(state.get("budget_limit", 100000.0))
        experience = state.get("experience_level", "intermediate")

        fin_risk = (spent / limit) if limit > 0 else 0.5
        if experience == "beginner":
            fin_risk += 0.15
        elif experience == "expert":
            fin_risk -= 0.10

        fin_risk = float(max(0.05, min(0.95, fin_risk)))

        # 5. Recommendation risk (Composite score summing operational factors)
        rec_risk = (
            weather_risk * 0.25 +
            crop_failure_risk * 0.30 +
            disease_risk * 0.25 +
            fin_risk * 0.20
        )

        return {
            "weather_risk": round(weather_risk, 2),
            "crop_failure_risk": round(crop_failure_risk, 2),
            "disease_risk": round(disease_risk, 2),
            "financial_risk": round(fin_risk, 2),
            "recommendation_risk": round(rec_risk, 2)
        }
