from typing import Any, Dict

from app.personalization.models import FarmDetails, FarmerProfile, LongTermMemory


class ProfileBuilder:
    """
    Builds a unified state representation from profile data and histories
    to seed predictions and risk engines.
    """
    def build_twin_state(
        self,
        profile: FarmerProfile,
        twin: FarmDetails,
        memory: LongTermMemory
    ) -> Dict[str, Any]:
        return {
            "farmer_id": profile.farmer_id,
            "name": profile.name,
            "language": profile.preferred_language,
            "experience_level": profile.experience_level,
            "risk_tolerance": profile.risk_tolerance,
            "budget_limit": profile.budget_limit,
            "budget_spent": profile.budget_spent,
            "land_size_acres": twin.land_size_acres,
            "village": twin.village,
            "district": twin.district,
            "state": twin.state,
            "climate_zone": twin.climate_zone,
            "crop_zone": twin.crop_zone,
            "crop_history": twin.crop_history,
            "soil_history": twin.soil_history,
            "equipment": twin.equipment,
            "livestock": twin.livestock,
            "irrigation_type": twin.irrigation_type,
            "scheme_history": twin.scheme_history,
            "conversations": memory.conversations,
            "feedback_history": memory.feedback_history,
            "historical_outcomes": memory.historical_outcomes,
        }
