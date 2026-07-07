import logging
from typing import Any, Dict

logger = logging.getLogger("kisan_mitra_ai.digital_twin.prediction_engine")

class PredictionEngine:
    """
    Forecasting model generating agricultural projections based on the farmer's Digital Twin details.
    """
    def predict(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Next crop prediction (Crop rotation heuristic)
        history = state.get("crop_history", [])
        last_crop = "Wheat"
        if history and isinstance(history, list) and isinstance(history[-1], dict):
            last_crop = history[-1].get("crop", "Wheat")

        # Rotate crop Wheat <-> Rice
        next_crop = "Rice" if last_crop.strip().lower() == "wheat" else "Wheat"

        # 2. Water demand estimation (Scaling with land size and irrigation type)
        land = float(state.get("land_size_acres", 2.0))
        irrigation = state.get("irrigation_type", "rainfed")

        # Base demand: 500k liters per acre (typical for seasonal cereals)
        base_demand = land * 500000.0
        if next_crop == "Rice":
            base_demand *= 1.5  # Rice is highly water-intensive

        if irrigation in ["drip", "sprinkler"]:
            water_demand_liters = base_demand * 0.6  # 40% efficiency gains
        elif irrigation == "canal":
            water_demand_liters = base_demand * 0.9
        else:
            water_demand_liters = base_demand * 1.15

        # 3. Disease probability estimation based on geography and crop selection
        state_name = str(state.get("state", "")).strip().lower()
        disease_name = "Rice Blast" if next_crop == "Rice" else "Wheat Rust"
        prob = 0.15

        # Regional hazard factor multipliers
        if state_name in ["punjab", "haryana"] and next_crop == "Wheat":
            prob = 0.35
        elif state_name in ["karnataka", "andhra pradesh"] and next_crop == "Rice":
            prob = 0.40

        # 4. Income Trend forecasting based on budget spend history and success ratio
        budget_spent = float(state.get("budget_spent", 0.0))
        budget_limit = float(state.get("budget_limit", 100000.0))
        outcomes = state.get("historical_outcomes", [])

        success_count = sum(1 for o in outcomes if isinstance(o, dict) and o.get("success", True))
        success_ratio = (success_count / len(outcomes)) if outcomes else 0.8

        trend_pct = 0.05 + (0.12 * success_ratio)
        if budget_spent > budget_limit * 0.85:
            trend_pct -= 0.15  # Budget overrun reduces profit margins

        # 5. Scheme eligibility changes check
        current_schemes = state.get("scheme_history", [])
        eligible_new = []

        # PM-Kisan eligibility (typically smallholders <= 5.0 acres)
        if "PM-Kisan" not in current_schemes and land <= 5.0:
            eligible_new.append("PM-Kisan")
        if "PMFBY" not in current_schemes:
            eligible_new.append("PMFBY")

        return {
            "next_crop": next_crop,
            "water_demand_liters": round(water_demand_liters, 2),
            "disease_probability": {
                "disease": disease_name,
                "probability": round(prob, 2)
            },
            "income_trend": {
                "trend": "upward" if trend_pct >= 0 else "downward",
                "growth_rate_pct": round(trend_pct * 100, 2)
            },
            "scheme_eligibility_changes": {
                "eligible_new_schemes": eligible_new,
                "status": "changed" if eligible_new else "stable"
            }
        }
