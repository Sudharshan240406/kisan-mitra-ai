from typing import Any, Dict, List


class ResponseValidator:
    """
    Validates consolidated agent responses for contradictions, low confidence indicators, and incomplete recommendations.
    """
    def __init__(self) -> None:
        pass

    def validate(self, response_data: Dict[str, Any]) -> List[str]:
        warnings = []

        confidence = response_data.get("confidence", 1.0)
        if confidence < 0.7:
            warnings.append(f"Low confidence evaluation score: {confidence:.2f}")

        # Check for gaps/missing information
        missing_info = response_data.get("missing_information", [])
        if missing_info:
            warnings.append(f"Incomplete profile parameters. Gaps detected in: {', '.join(missing_info)}")

        # Check for simple semantic contradictions
        rec_text = response_data.get("recommendation", "").lower()
        if "not eligible" in rec_text and "eligible for" in rec_text:
            warnings.append("Potential contradiction: recommendation text refers to both eligibility and non-eligibility outcomes.")

        return warnings
