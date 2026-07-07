import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from app.digital_twin.prediction_engine import PredictionEngine
from app.digital_twin.profile_builder import ProfileBuilder
from app.digital_twin.recommendation_engine import RecommendationEngine
from app.digital_twin.risk_engine import RiskEngine
from app.digital_twin.twin_engine import PredictiveTwin
from app.personalization.models import FarmDetails, FarmerProfile, LongTermMemory

logger = logging.getLogger("kisan_mitra_ai.digital_twin.twin_manager")

class TwinManager:
    """
    Orchestration manager coordinating predictive model pipelines, calculations,
    and syncing back outcomes to personalization profiles.
    """
    def __init__(self, container: Any, db_path: str = "./data/predictive_twins.json") -> None:
        self.container = container
        self.db_path = db_path
        self.profile_builder = ProfileBuilder()
        self.prediction_engine = PredictionEngine()
        self.risk_engine = RiskEngine()
        self.recommendation_engine = RecommendationEngine()

        self.predictive_twins: Dict[str, PredictiveTwin] = {}
        self.load_from_disk()

    def get_twin(self, farmer_id: str) -> Optional[PredictiveTwin]:
        # Try local cache
        if farmer_id in self.predictive_twins:
            return self.predictive_twins[farmer_id]

        # Hydrate from personalization platform
        p_platform = self.container.personalization_platform
        profile = p_platform.profiles.get(farmer_id)
        twin = p_platform.twins.get(farmer_id)
        memory = p_platform.memories.get(farmer_id)

        if not profile:
            # Register a default profile to guarantee loading works
            profile = FarmerProfile(farmer_id=farmer_id, name="Farmer Ramesh")
            p_platform.profiles[farmer_id] = profile
        if not twin:
            twin = FarmDetails(
                farmer_id=farmer_id,
                land_size_acres=2.0,
                village="Kila Raipur",
                district="Ludhiana",
                state="Punjab"
            )
            p_platform.twins[farmer_id] = twin
        if not memory:
            memory = LongTermMemory(farmer_id=farmer_id)
            p_platform.memories[farmer_id] = memory

        # Build state
        state = self.profile_builder.build_twin_state(profile, twin, memory)

        # Calculate initial predictions and risks
        predictions = self.prediction_engine.predict(state)
        risks = self.risk_engine.calculate_risks(state, predictions)
        recs = self.recommendation_engine.generate_proactive_recommendations(state, predictions, risks)

        pred_twin = PredictiveTwin(
            farmer_id=farmer_id,
            profile=profile,
            twin=twin,
            predictions=predictions,
            risks=risks,
            recommendations=recs,
            updated_at=time.time()
        )
        self.predictive_twins[farmer_id] = pred_twin
        self.save_to_disk()
        return pred_twin

    def update_twin(self, twin: PredictiveTwin) -> PredictiveTwin:
        self.predictive_twins[twin.farmer_id] = twin

        # Synchronize back to personalization platform
        p_platform = self.container.personalization_platform
        p_platform.profiles[twin.farmer_id] = twin.profile
        p_platform.twins[twin.farmer_id] = twin.twin
        p_platform.save_to_disk()

        self.save_to_disk()
        return twin

    def predict(self, farmer_id: str) -> Dict[str, Any]:
        twin = self.get_twin(farmer_id)
        if not twin:
            return {}
        p_platform = self.container.personalization_platform
        memory = p_platform.memories.get(farmer_id) or LongTermMemory(farmer_id=farmer_id)
        state = self.profile_builder.build_twin_state(twin.profile, twin.twin, memory)

        predictions = self.prediction_engine.predict(state)
        twin.predictions = predictions
        twin.updated_at = time.time()
        self.save_to_disk()
        return predictions

    def calculate_risk(self, farmer_id: str) -> Dict[str, Any]:
        twin = self.get_twin(farmer_id)
        if not twin:
            return {}
        p_platform = self.container.personalization_platform
        memory = p_platform.memories.get(farmer_id) or LongTermMemory(farmer_id=farmer_id)
        state = self.profile_builder.build_twin_state(twin.profile, twin.twin, memory)

        risks = self.risk_engine.calculate_risks(state, twin.predictions)
        twin.risks = risks
        twin.updated_at = time.time()
        self.save_to_disk()
        return risks

    def generate_recommendations(self, farmer_id: str) -> List[Dict[str, Any]]:
        twin = self.get_twin(farmer_id)
        if not twin:
            return []
        p_platform = self.container.personalization_platform
        memory = p_platform.memories.get(farmer_id) or LongTermMemory(farmer_id=farmer_id)
        state = self.profile_builder.build_twin_state(twin.profile, twin.twin, memory)

        recs = self.recommendation_engine.generate_proactive_recommendations(state, twin.predictions, twin.risks)
        twin.recommendations = recs
        twin.updated_at = time.time()
        self.save_to_disk()
        return recs

    def update_twin_from_interaction(self, farmer_id: str, query: str, response: str) -> None:
        """
        Extracts information from interaction to update twin characteristics,
        and triggers a full refresh of predictions, risks, and proactive recommendations.
        """
        twin = self.get_twin(farmer_id)
        if not twin:
            return

        # Parse query/response for new crops or locations
        query_lower = query.lower()
        response_lower = response.lower()

        # 1. Update crop history if a crop is mentioned
        for crop in ["wheat", "rice", "cotton", "maize", "mustard"]:
            if crop in query_lower or crop in response_lower:
                crop_title = crop.capitalize()
                if not any(c.get("crop") == crop_title for c in twin.twin.crop_history):
                    twin.twin.crop_history.append({
                        "crop": crop_title,
                        "planted_at": time.time(),
                        "yield_kg": 2200.0
                    })
                    logger.info(f"[TwinManager] Extracted and added crop '{crop_title}' to crop history.")

        # 2. Update location/district if mentioned
        if "ludhiana" in query_lower:
            twin.twin.district = "Ludhiana"
            twin.twin.state = "Punjab"
        elif "dharwad" in query_lower:
            twin.twin.district = "Dharwad"
            twin.twin.state = "Karnataka"

        # Re-run prediction and risk pipelines
        p_platform = self.container.personalization_platform
        memory = p_platform.memories.get(farmer_id) or LongTermMemory(farmer_id=farmer_id)
        state = self.profile_builder.build_twin_state(twin.profile, twin.twin, memory)

        twin.predictions = self.prediction_engine.predict(state)
        twin.risks = self.risk_engine.calculate_risks(state, twin.predictions)
        twin.recommendations = self.recommendation_engine.generate_proactive_recommendations(
            state, twin.predictions, twin.risks
        )
        twin.updated_at = time.time()

        # Sync back to platform
        self.update_twin(twin)

    def load_from_disk(self) -> None:
        if not os.path.exists(self.db_path):
            return
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for fid, item in data.items():
                self.predictive_twins[fid] = PredictiveTwin(**item)
            logger.info(f"Loaded {len(self.predictive_twins)} predictive twins from disk.")
        except Exception as e:
            logger.error(f"Failed to load predictive twins from disk: {e}")

    def save_to_disk(self) -> None:
        try:
            dir_name = os.path.dirname(self.db_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            data = {fid: item.model_dump() for fid, item in self.predictive_twins.items()}
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save predictive twins to disk: {e}")
