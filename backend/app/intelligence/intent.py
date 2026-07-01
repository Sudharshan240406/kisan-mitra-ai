from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    WEATHER = "Weather"
    DISEASE = "Disease"
    MARKET = "Market"
    GOVERNMENT_SCHEME = "Government Scheme"
    FINANCE = "Finance"
    IRRIGATION = "Irrigation"
    SOIL = "Soil"
    CROP_RECOMMENDATION = "Crop Recommendation"
    FERTILIZER = "Fertilizer"
    PEST = "Pest"
    INSURANCE = "Insurance"
    GENERAL_AGRICULTURE = "General Agriculture"
    MIXED_QUERY = "Mixed Query"
    UNKNOWN = "Unknown"

class IntentResult(BaseModel):
    """
    Standard envelope representing the output of the Intent Detection Engine.
    """
    detected_intents: list[IntentType] = Field(..., description="List of recognized agricultural intent categories.")
    confidence: dict[IntentType, float] = Field(..., description="Intent confidence scoring maps.")
    ambiguity_score: float = Field(..., description="Score indicating intent confusion/ambiguity level.")
    matched_keywords: list[str] = Field(default_factory=list, description="Keywords matched in the query text.")
    extracted_hints: list[str] = Field(default_factory=list, description="Syntactic patterns extracted from the query.")
    planner_hints: dict[str, Any] = Field(default_factory=dict, description="Metadata flags passed to the execution planner.")

class IntentEngine:
    """
    Rule-based parser mapping agricultural keyword mappings to candidate intents.
    Computes confidences, ambiguity spreads, and validates multi-intent scenarios.
    """
    def __init__(self) -> None:
        # Standardized domain matching keyword registries
        self._keyword_registry: dict[IntentType, list[str]] = {
            IntentType.WEATHER: ["weather", "rain", "temperature", "temp", "climate", "monsoon", "forecast", "wind", "humidity", "storm"],
            IntentType.DISEASE: ["disease", "rust", "blast", "spot", "rot", "mildew", "wilt", "infected", "fungal", "symptom", "blight", "muff"],
            IntentType.MARKET: ["market", "price", "rate", "cost", "mandi", "sell", "trade", "value", "commodity", "price index"],
            IntentType.GOVERNMENT_SCHEME: ["scheme", "subsidy", "welfare", "yojana", "pm-kisan", "government", "benefit", "subsidy grant"],
            IntentType.FINANCE: ["loan", "credit", "finance", "kcc", "bank", "interest", "debt", "capital"],
            IntentType.IRRIGATION: ["irrigation", "water", "drip", "sprinkler", "borewell", "pump", "canal", "watering"],
            IntentType.SOIL: ["soil", "ph", "sand", "clay", "loam", "nutrient", "earth", "dirt", "fertilization level"],
            IntentType.CROP_RECOMMENDATION: ["recommendation", "recommend", "crop to grow", "grow", "suitable crop", "plant", "select crop"],
            IntentType.FERTILIZER: ["fertilizer", "urea", "npk", "manure", "compost", "phosphate", "potash"],
            IntentType.PEST: ["pest", "bug", "insect", "caterpillar", "infestation", "spray", "pesticide", "aphid", "locust"],
            IntentType.INSURANCE: ["insurance", "claim", "damage", "crop loss", "compensation", "bima", "payout"],
            IntentType.GENERAL_AGRICULTURE: ["farming", "agriculture", "farmer", "advisory", "cultivation", "harvest"]
        }

    def detect_intents(self, query: str) -> IntentResult:
        normalized_query = query.lower()

        # 1. Check matching keywords
        confidences: dict[IntentType, float] = {}
        matched_keywords_list: list[str] = []

        for intent, keywords in self._keyword_registry.items():
            matches = [kw for kw in keywords if kw in normalized_query]
            if matches:
                matched_keywords_list.extend(matches)
                # Compute score as matches count relative to query keyword concentration
                confidences[intent] = min(len(matches) * 0.4, 1.0)

        # 2. Resolve no-matches to Unknown
        if not confidences:
            return IntentResult(
                detected_intents=[IntentType.UNKNOWN],
                confidence={IntentType.UNKNOWN: 1.0},
                ambiguity_score=0.0,
                matched_keywords=[],
                extracted_hints=["No recognized keyword matches found."],
                planner_hints={"fallback_required": True}
            )

        # Sort scores to identify top candidates
        sorted_intents = sorted(confidences.items(), key=lambda x: x[1], reverse=True)
        top_intent, top_score = sorted_intents[0]

        # Identify ambiguity (closeness of the second score)
        ambiguity_val = 0.0
        if len(sorted_intents) > 1:
            _, second_score = sorted_intents[1]
            # If the difference is small, ambiguity is high
            difference = top_score - second_score
            ambiguity_val = max(1.0 - difference, 0.0)

        # Determine candidate intents: any category exceeding 0.3 threshold
        selected_intents = [intent for intent, score in confidences.items() if score >= 0.3]
        if not selected_intents:
            selected_intents = [top_intent]

        # Handle mixed query scenario
        if len(selected_intents) > 1:
            selected_intents.append(IntentType.MIXED_QUERY)
            confidences[IntentType.MIXED_QUERY] = 0.8

        return IntentResult(
            detected_intents=selected_intents,
            confidence=confidences,
            ambiguity_score=ambiguity_val,
            matched_keywords=list(set(matched_keywords_list)),
            extracted_hints=[f"Identified agricultural targets: {list(confidences.keys())}"],
            planner_hints={"multi_intent": len(selected_intents) > 1}
        )
