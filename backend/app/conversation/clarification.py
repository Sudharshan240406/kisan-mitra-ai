from pydantic import BaseModel, Field


class ClarificationRequest(BaseModel):
    """
    Structured request identifying missing variables and ordering clarifications.
    """
    category: str = Field(..., description="Target query category (e.g. Disease, Weather).")
    missing_fields: list[str] = Field(..., description="List of properties requiring farmer input.")
    priority_field: str = Field(..., description="The highest priority missing property.")
    guidance_cues: dict[str, str] = Field(default_factory=dict, description="Guidance labels explaining prompt relevance.")


class ClarificationEngine:
    """
    Clarification processor auditing intent data slots to identify missing parameters.
    """
    def __init__(self) -> None:
        self._cues = {
            "disease": {
                "symptoms": "Please describe crop leaf color changes or pathological signs.",
                "crop": "Please specify the crop suffering from the infection."
            },
            "weather": {
                "location": "Please specify your geographic village, taluk, or district.",
                "duration": "Please specify forecast duration (e.g. tomorrow, next week)."
            },
            "market": {
                "crop": "Please identify the commodity price mandi query crop.",
                "location": "Please specify your target market name or regional trading center."
            },
            "government": {
                "farmer_id": "Please provide your unique farmer registration identity.",
                "scheme_title": "Please provide the official scheme name or subsidy program."
            },
            "finance": {
                "loan_type": "Please identify target credit category (e.g. KCC, crop loan).",
                "bank": "Please provide your active banking partner name."
            },
            "soil": {
                "pH": "Please specify target soil chemical pH levels.",
                "location": "Please provide location parameters for soil checks."
            },
            "mixed queries": {
                "crop": "Please identify the primary target crop of interest.",
                "location": "Please specify the reference location parameters."
            }
        }

    def generate_request(self, category: str, missing_fields: list[str]) -> ClarificationRequest:
        """
        Builds a structured clarification request without natural language generation.
        """
        if not missing_fields:
            raise ValueError("No missing fields specified for clarification.")

        cat_key = category.strip().lower()
        if cat_key not in self._cues:
            # Fallback to mixed queries cues
            cat_key = "mixed queries"

        cues_map = self._cues[cat_key]

        # Prioritize required information: select first missing field that has a cue, or default to the first missing field
        priority_field = missing_fields[0]
        for field in missing_fields:
            if field in cues_map:
                priority_field = field
                break

        # Map matching guidance cues
        resolved_cues = {}
        for field in missing_fields:
            resolved_cues[field] = cues_map.get(field, f"Please provide reference value for '{field}'.")

        return ClarificationRequest(
            category=category,
            missing_fields=missing_fields,
            priority_field=priority_field,
            guidance_cues=resolved_cues
        )
