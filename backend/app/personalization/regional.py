"""
Kisan Mitra AI — Regional Intelligence
======================================
Adapts farmer advice by mapping physical coordinates, states, districts,
and villages to agro-climatic zones, local Mandi markets, and language rules.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("kisan_mitra_ai.personalization.regional")


class RegionalIntelligenceService:
    """
    Enables regional adjustments based on state, district, and village.
    """
    CLIMATE_MAP: Dict[str, str] = {
        "punjab": "Trans-Gangetic Plains Region",
        "haryana": "Trans-Gangetic Plains Region",
        "karnataka": "Southern Plateau and Hills Region",
        "maharashtra": "Western Plateau and Hills Region",
        "uttar pradesh": "Upper Gangetic Plains Region",
        "rajasthan": "Western Dry Region",
    }

    CROP_CALENDAR: Dict[str, Dict[str, Any]] = {
        "wheat": {
            "sowing_months": ["November", "December"],
            "harvest_months": ["April", "May"],
            "climate_requirement": "Cool winter, moderate rainfall",
        },
        "rice": {
            "sowing_months": ["June", "July"],
            "harvest_months": ["October", "November"],
            "climate_requirement": "Warm, humid, high water demand",
        },
    }

    LOCAL_SCHEMES: Dict[str, list[str]] = {
        "punjab": ["Kahu-Kheti Scheme", "Punjab Crop Subsidy"],
        "karnataka": ["Raitha Siri", "Krishi Bhagya Scheme"],
    }

    def get_agro_climatic_zone(self, state: str) -> str:
        return self.CLIMATE_MAP.get(state.lower().strip(), "Western Plateau and Hills Region")

    def get_regional_crop_calendar(self, crop: str) -> Optional[Dict[str, Any]]:
        return self.CROP_CALENDAR.get(crop.lower().strip())

    def get_state_schemes(self, state: str) -> list[str]:
        return self.LOCAL_SCHEMES.get(state.lower().strip(), ["State General Farmer Support Program"])

    def adapt_vernacular_names(self, term: str, language: str) -> str:
        """Translates common agricultural terms for local region templates."""
        translations = {
            "wheat": {"hi": "गेहूं", "kn": "ಗೋಧಿ", "te": "గోధుమలు", "ta": "கோதுமை"},
            "rice": {"hi": "चावल", "kn": "ಭತ್ತ", "te": "వరి", "ta": "அரிசி"},
            "water": {"hi": "पानी", "kn": "ನೀರು", "te": "నీరు", "ta": "தண்ணீர்"},
            "fertilizer": {"hi": "खाद", "kn": "ಗೊಬ್ಬರ", "te": "ఎరువులు", "ta": "உரம்"},
        }
        return translations.get(term.lower().strip(), {}).get(language.lower().strip(), term)

    def get_regional_context(self, state: str, district: str, village: str) -> dict[str, Any]:
        """
        Combines geography variables into a consolidated regional parameter dictionary.
        """
        zone = self.get_agro_climatic_zone(state)
        schemes = self.get_state_schemes(state)
        return {
            "state": state,
            "district": district,
            "village": village,
            "agro_climatic_zone": zone,
            "local_schemes": schemes,
            "primary_market_name": f"{district} Mandi",
        }
