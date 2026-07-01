from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class EntityType(str, Enum):
    CROP = "Crop"
    DISEASE = "Disease"
    COMMODITY = "Commodity"
    VILLAGE = "Village"
    TALUK = "Taluk"
    DISTRICT = "District"
    STATE = "State"
    COUNTRY = "Country"
    SEASON = "Season"
    LANGUAGE = "Language"
    FARMER = "Farmer"
    GOVERNMENT_SCHEME = "Government Scheme"
    WEATHER_EVENT = "Weather Event"
    DATE = "Date"
    TIME = "Time"

class ExtractedEntity(BaseModel):
    """
    Metadata representation of an individual extracted entity record.
    """
    entity_type: EntityType = Field(..., description="Target entity class type.")
    value: str = Field(..., description="The parsed canonical value.")
    confidence: float = Field(default=1.0, description="Confidence rating for extraction.")
    matched_text: str = Field(..., description="Query substring that triggered this match.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible JSON metadata properties.")

class EntityResult(BaseModel):
    """
    Envelope grouping all entities resolved from a farmer query.
    """
    entities: list[ExtractedEntity] = Field(..., description="List of recognized entity objects.")
    extracted_types: list[EntityType] = Field(..., description="Convenience index of unique types extracted.")

class EntityExtractor:
    """
    Rule-based extractor mapping query substrings to structured agricultural entities.
    """
    def __init__(self) -> None:
        # Dictionary registry maps for simple entity lookup matching
        self._lookup_registry: dict[EntityType, list[str]] = {
            EntityType.CROP: ["wheat", "rice", "cotton", "maize", "barley", "sugarcane", "tomato", "jowar", "bajra"],
            EntityType.DISEASE: ["rust", "blast", "spot", "mildew", "rot", "blight", "wilt"],
            EntityType.COMMODITY: ["wheat", "rice", "cotton", "soybean", "mustard", "onion", "potato"],
            EntityType.VILLAGE: ["village", "mandi", "rampura", "pipariya"],
            EntityType.TALUK: ["taluk", "tehsil", "block", "haveli"],
            EntityType.DISTRICT: ["district", "amritsar", "ludhiana", "pune", "nagpur", "nashik"],
            EntityType.STATE: ["punjab", "maharashtra", "haryana", "karnataka", "gujarat", "bihar"],
            EntityType.COUNTRY: ["india"],
            EntityType.SEASON: ["kharif", "rabi", "zaid", "summer", "winter", "monsoon"],
            EntityType.LANGUAGE: ["english", "hindi", "punjabi", "marathi", "telugu", "tamil"],
            EntityType.FARMER: ["ramesh", "suresh", "anil", "kamal", "gopal"],
            EntityType.GOVERNMENT_SCHEME: ["pm-kisan", "pm-pranam", "fasal bima", "kcc", "subsidies"],
            EntityType.WEATHER_EVENT: ["rain", "drought", "hail", "frost", "flood", "heatwave", "shower"],
            EntityType.DATE: ["today", "tomorrow", "yesterday", "monday", "tuesday"],
            EntityType.TIME: ["morning", "evening", "afternoon", "night", "daytime"]
        }

    def extract_entities(self, query: str) -> EntityResult:
        normalized_query = query.lower()
        extracted: list[ExtractedEntity] = []
        unique_types = set()

        for etype, keywords in self._lookup_registry.items():
            for kw in keywords:
                # Check for keyword boundaries to avoid false positives (e.g. "rain" in "grain")
                # For basic rule matching we check substring matches
                if kw in normalized_query:
                    # Resolve matches
                    entity = ExtractedEntity(
                        entity_type=etype,
                        value=kw.capitalize(),
                        confidence=1.0,
                        matched_text=kw
                    )
                    extracted.append(entity)
                    unique_types.add(etype)

        return EntityResult(
            entities=extracted,
            extracted_types=list(unique_types)
        )
