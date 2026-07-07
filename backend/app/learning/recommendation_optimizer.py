import logging
from typing import Any, Dict

from app.learning.feedback_store import RecommendationFeedback

logger = logging.getLogger("kisan_mitra_ai.learning.recommendation_optimizer")

class RecommendationOptimizer:
    """
    Learns farmer and cohort preferences over time:
    - Preferred welfare schemes (e.g. PM-Kisan)
    - Frequently accepted advice categories (e.g. Organic, Fertilizers)
    - Regional preferences (e.g. State-level schemes)
    - Language preferences (e.g. Punjabi/Kannada scheme response styles)
    """
    def __init__(self) -> None:
        self.scheme_weights: Dict[str, float] = {}
        self.advice_weights: Dict[str, float] = {}
        self.regional_weights: Dict[str, Dict[str, float]] = {}
        self.language_weights: Dict[str, Dict[str, float]] = {}

    def update_preferences(self, feedback: RecommendationFeedback) -> None:
        """
        Updates preference weights based on farmer acceptance or rejection feedback.
        """
        meta = feedback.metadata
        scheme = meta.get("scheme") or feedback.recommendation_id
        advice_type = meta.get("advice_type") or "general"
        region = meta.get("region")  # state or district
        language = meta.get("language") or "en"

        # Calculate update step
        step = 0.0
        if feedback.accepted:
            step = 0.10
        elif feedback.rejected:
            step = -0.15

        if step == 0.0:
            return

        # 1. Update preferred schemes
        self.scheme_weights[scheme] = float(max(-1.0, min(1.0, self.scheme_weights.get(scheme, 0.0) + step)))

        # 2. Update advice types
        self.advice_weights[advice_type] = float(max(-1.0, min(1.0, self.advice_weights.get(advice_type, 0.0) + step)))

        # 3. Update regional preferences
        if region:
            if region not in self.regional_weights:
                self.regional_weights[region] = {}
            current_reg = self.regional_weights[region].get(scheme, 0.0)
            self.regional_weights[region][scheme] = float(max(-1.0, min(1.0, current_reg + step)))

        # 4. Update language preferences
        if language:
            if language not in self.language_weights:
                self.language_weights[language] = {}
            current_lang = self.language_weights[language].get(scheme, 0.0)
            self.language_weights[language][scheme] = float(max(-1.0, min(1.0, current_lang + step)))

        logger.info(
            f"Preference optimized for scheme='{scheme}', advice_type='{advice_type}', "
            f"region='{region}', lang='{language}'. Step: {step:+.2f}"
        )

    def score_recommendation(self, rec: Dict[str, Any], context: Dict[str, Any]) -> float:
        """
        Calculates a preference score boost (between -0.5 and +0.5) for a candidate recommendation.
        """
        scheme = rec.get("id") or rec.get("scheme_id") or "general"
        advice_type = rec.get("category") or rec.get("advice_type") or "general"
        region = context.get("region") or context.get("location")
        language = context.get("language") or "en"

        boost = 0.0

        # Scheme boost
        boost += self.scheme_weights.get(scheme, 0.0) * 0.2

        # Advice type boost
        boost += self.advice_weights.get(advice_type, 0.0) * 0.1

        # Regional boost
        if region and region in self.regional_weights:
            boost += self.regional_weights[region].get(scheme, 0.0) * 0.15

        # Language boost
        if language and language in self.language_weights:
            boost += self.language_weights[language].get(scheme, 0.0) * 0.10

        # Cap the composite preference score boost
        return float(max(-0.5, min(0.5, boost)))
