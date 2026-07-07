from typing import Any, Dict, List


class RecommendationEngine:
    """
    Generates proactive recommendations based on predictive forecasts and farm risks.
    """
    def generate_proactive_recommendations(
        self,
        state: Dict[str, Any],
        predictions: Dict[str, Any],
        risks: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        recs = []

        # 1. Check crop failure risk and recommend infrastructure changes
        crop_failure_risk = risks.get("crop_failure_risk", 0.0)
        irrigation = state.get("irrigation_type", "rainfed")

        if crop_failure_risk > 0.50 and irrigation == "rainfed":
            recs.append({
                "id": "twin_rec_drip_irrigation",
                "category": "infrastructure",
                "title": "Upgrade to Micro-Irrigation (Drip/Sprinkler)",
                "recommendation": "Your predicted crop failure risk is elevated due to rainfed watering. Adopting sprinkler or drip setups will optimize water conservation.",
                "confidence": 0.85,
                "urgency": "high"
            })

        # 2. Check predicted disease probability and suggest preventative pathology treatments
        disease_prob = predictions.get("disease_probability", {}).get("probability", 0.0)
        disease_name = predictions.get("disease_probability", {}).get("disease", "Crop Pathology")

        if disease_prob > 0.30:
            recs.append({
                "id": "twin_rec_disease_spraying",
                "category": "crop_pathology",
                "title": f"Preemptive {disease_name} Prevention",
                "recommendation": f"Forecasts indicate a {int(disease_prob * 100)}% chance of {disease_name}. Apply preventative biological treatments or neem oils.",
                "confidence": 0.90,
                "urgency": "high"
            })

        # 3. Next Crop Advice based on rotation
        next_crop = predictions.get("next_crop", "Wheat")
        recs.append({
            "id": "twin_rec_crop_sowing",
            "category": "agronomy",
            "title": f"Prepare for {next_crop} Cycle Sowing",
            "recommendation": f"Crop history indicates rotation cycle suitability for {next_crop} sowing. Procure seeds from certified providers.",
            "confidence": 0.80,
            "urgency": "medium"
        })

        # 4. Welfare Scheme matches
        new_eligible = predictions.get("scheme_eligibility_changes", {}).get("eligible_new_schemes", [])
        for scheme in new_eligible:
            recs.append({
                "id": f"twin_rec_apply_{scheme.lower().replace('-', '_')}",
                "category": "government_scheme",
                "title": f"Apply for {scheme}",
                "recommendation": f"You match the eligibility criteria for {scheme}. Apply via regional portals to obtain welfare support.",
                "confidence": 0.95,
                "urgency": "high"
            })

        return recs
