import re
from typing import Any, TypedDict, List

class IntentResult(TypedDict):
    intent: str
    confidence: float
    entities: List[str]

class IntentRouter:
    """
    Intelligently maps queries to core Intents and extracts semantic entity keys.
    """
    def __init__(self) -> None:
        self.rules = [
            (r"(scheme|yojana|welfare|subsidy|pension|benefit|qualify)", "Government Scheme"),
            (r"(weather|rain|temp|temperature|climate|monsoon|humidity)", "Weather"),
            (r"(price|rate|market|mandi|msp|cost|sell|buy)", "Market Price"),
            (r"(disease|pest|rot|spot|leaf|damage|insect|fungus|blight)", "Crop Disease"),
            (r"(document|aadhaar|pan|passbook|checklist|papers|verification)", "Document Help"),
            (r"(hello|hi|namaste|greeting|welcome|hey)", "Greeting"),
            (r"(listen|speak|voice|record|audio|tts|stt)", "Voice Command")
        ]
        
        self.entity_patterns = {
            "crop": r"\b(wheat|rice|cotton|soybean|sugarcane|maize|crop|crops)\b",
            "location": r"\b(punjab|maharashtra|karnataka|haryana|village|district|state)\b",
            "document": r"\b(aadhaar|pan|passbook|land records|identity)\b"
        }

    def detect_intent(self, query: str) -> IntentResult:
        query_lower = query.lower()
        
        detected_intent = "General Question"
        confidence = 0.80
        
        for pattern, intent in self.rules:
            if re.search(pattern, query_lower):
                detected_intent = intent
                confidence = 0.95
                break
                
        # Extract entities
        entities = []
        for entity_type, pat in self.entity_patterns.items():
            matches = re.findall(pat, query_lower)
            for m in matches:
                entities.append(f"{entity_type}:{m}")
                
        return {
            "intent": detected_intent,
            "confidence": confidence,
            "entities": entities
        }
