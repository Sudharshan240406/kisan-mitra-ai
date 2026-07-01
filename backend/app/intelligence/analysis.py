import time
from typing import Any

from app.intelligence.entity import EntityExtractor, EntityResult, EntityType
from app.intelligence.intent import IntentEngine, IntentResult, IntentType
from pydantic import BaseModel, Field


class MissingInformationReport(BaseModel):
    """
    Detailed report indicating what data fields are missing from user context.
    """
    missing_fields: list[str] = Field(..., description="List of fields that need clarification.")
    is_complete: bool = Field(..., description="True if no required fields are missing.")
    validation_cues: dict[str, str] = Field(default_factory=dict, description="Guidance hints indicating why the fields are needed.")

class QueryAnalysis(BaseModel):
    """
    Unified container summarizing intent, entities, missing fields, and metadata for a query.
    """
    raw_query: str = Field(..., description="The original raw input string.")
    normalized_query: str = Field(..., description="Cleaned, normalized input string.")
    language: str = Field("en", description="Detected language classification.")
    entities: EntityResult = Field(..., description="Aggregated extracted entity list.")
    intents: IntentResult = Field(..., description="Detected user intent categories.")
    ambiguity: float = Field(..., description="Overall intent ambiguity rating.")
    confidence: float = Field(..., description="Overall execution confidence scoring.")
    missing_information: MissingInformationReport = Field(..., description="Detected gaps/missing variables report.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extensible execution context metadata.")

class MissingInformationDetector:
    """
    Analyzes intent and entity pairings to identify gaps in required request parameters.
    """
    def detect_missing(self, intents: IntentResult, entities: EntityResult) -> MissingInformationReport:
        missing: list[str] = []
        cues: dict[str, str] = {}

        # Determine extracted types checklist
        types = set(entities.extracted_types)

        for intent in intents.detected_intents:
            if intent == IntentType.WEATHER:
                # Weather inquiries need geographic region location details
                location_types = {EntityType.VILLAGE, EntityType.TALUK, EntityType.DISTRICT, EntityType.STATE}
                if not location_types.intersection(types):
                    missing.append("location")
                    cues["location"] = "A village, district, or state is required to fetch accurate weather forecasts."

            elif intent == IntentType.DISEASE:
                # Disease diagnosis needs the target Crop type
                if EntityType.CROP not in types:
                    missing.append("crop")
                    cues["crop"] = "Crop type is required to identify disease diagnostics patterns."
                if EntityType.DISEASE not in types:
                    # Missing symptoms / disease indicators
                    missing.append("symptoms")
                    cues["symptoms"] = "Symptom descriptions or disease indicators are required."

            elif intent == IntentType.MARKET:
                # Market prices require commodity and location
                if EntityType.COMMODITY not in types and EntityType.CROP not in types:
                    missing.append("commodity")
                    cues["commodity"] = "A crop or commodity name is required to look up trading prices."
                location_types = {EntityType.VILLAGE, EntityType.TALUK, EntityType.DISTRICT, EntityType.STATE}
                if not location_types.intersection(types):
                    missing.append("location")
                    cues["location"] = "A market location or district is required for mandi rates lookup."

            elif intent == IntentType.GOVERNMENT_SCHEME:
                # Schemes need crop or farmer descriptors
                if EntityType.CROP not in types and EntityType.FARMER not in types:
                    missing.append("context_qualifiers")
                    cues["context_qualifiers"] = "Crop or land descriptors help match relevant schemes."

        return MissingInformationReport(
            missing_fields=missing,
            is_complete=len(missing) == 0,
            validation_cues=cues
        )

class QueryAnalyzer:
    """
    Coordinates Intent, Entity, and Missing Information detection into a single QueryAnalysis.
    """
    def __init__(self) -> None:
        self.intent_engine = IntentEngine()
        self.entity_extractor = EntityExtractor()
        self.missing_detector = MissingInformationDetector()

    def analyze(self, query: str, context_lang: str = "en") -> QueryAnalysis:
        normalized = query.strip().lower()

        # 1. Run detectors
        intents = self.intent_engine.detect_intents(query)
        entities = self.entity_extractor.extract_entities(query)
        missing = self.missing_detector.detect_missing(intents, entities)

        # Calculate combined confidence (mean of primary intent and entities match presence)
        primary_intent_score = 0.0
        if intents.detected_intents:
            primary_intent_score = intents.confidence.get(intents.detected_intents[0], 0.5)
        entity_weight = 1.0 if entities.entities else 0.5
        combined_confidence = (primary_intent_score + entity_weight) / 2.0

        return QueryAnalysis(
            raw_query=query,
            normalized_query=normalized,
            language=context_lang,
            entities=entities,
            intents=intents,
            ambiguity=intents.ambiguity_score,
            confidence=combined_confidence,
            missing_information=missing,
            metadata={"processed_timestamp": time.time()}
        )
