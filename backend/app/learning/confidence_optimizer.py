import logging
from typing import Dict, Optional

from app.learning.feedback_store import RecommendationFeedback

logger = logging.getLogger("kisan_mitra_ai.learning.confidence_optimizer")

class ConfidenceOptimizer:
    """
    Optimizes AI recommendation confidence based on historical outcomes and feedback.
    Increases confidence when recommendations succeed, and decreases it when they fail.
    """
    def __init__(self) -> None:
        # Tracks historical offsets for crops and regions
        self.crop_offsets: Dict[str, float] = {}
        self.region_offsets: Dict[str, float] = {}

    def get_optimized_confidence(
        self,
        base_confidence: float,
        crop: Optional[str] = None,
        region: Optional[str] = None
    ) -> float:
        """
        Applies learned crop and regional offsets to a baseline confidence rating.
        """
        offset = 0.0
        if crop and crop in self.crop_offsets:
            offset += self.crop_offsets[crop]
        if region and region in self.region_offsets:
            offset += self.region_offsets[region]

        optimized = base_confidence + offset
        return float(min(1.0, max(0.1, optimized)))

    def update_offsets(self, feedback: RecommendationFeedback) -> None:
        """
        Adjusts crop and regional confidence offsets based on success or failure of recommendations.
        """
        crop = feedback.metadata.get("crop")
        region = feedback.metadata.get("region") # state or district

        # Calculate offset adjustment step
        step = 0.0
        if feedback.accepted:
            step = 0.02
        elif feedback.rejected:
            step = -0.05

        if step == 0.0:
            return

        if crop:
            current = self.crop_offsets.get(crop, 0.0)
            # Cap offset range between -0.20 and +0.20
            self.crop_offsets[crop] = float(min(0.20, max(-0.20, current + step)))
            logger.info(f"Updated confidence offset for crop '{crop}': {self.crop_offsets[crop]:+.3f}")

        if region:
            current = self.region_offsets.get(region, 0.0)
            self.region_offsets[region] = float(min(0.20, max(-0.20, current + step)))
            logger.info(f"Updated confidence offset for region '{region}': {self.region_offsets[region]:+.3f}")

    def optimize_confidence(self, current_confidence: float, feedback: RecommendationFeedback) -> float:
        """
        Returns an adjusted confidence level directly for an individual feedback outcome.
        """
        self.update_offsets(feedback)
        
        val = current_confidence
        if feedback.accepted:
            val = min(1.0, current_confidence + 0.05)
        elif feedback.rejected:
            val = max(0.1, current_confidence - 0.10)
            
        return round(float(val), 4)
