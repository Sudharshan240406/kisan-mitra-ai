from typing import Any, Dict, List


class ResponseBuilder:
    """
    Builds standard unified response schema structures.
    """
    def __init__(self) -> None:
        pass

    def build_trusted_recommendation(
        self,
        summary: str,
        recommendation: str,
        confidence: float,
        reasoning: List[str],
        sources: List[str],
        evidence: List[Dict[str, Any]],
        warnings: List[str],
        missing_information: List[str],
        follow_up_required: List[str],
        safety_assessment: Dict[str, Any],
        reasoning_graph_ref: str
    ) -> Dict[str, Any]:
        """
        Creates a dictionary compatible with the TrustedRecommendation schema.
        """
        return {
            "summary": summary,
            "recommendation": recommendation,
            "evidence": evidence,
            "confidence": confidence,
            "risk": safety_assessment.get("risk_score", 0.0),
            "reasoning": reasoning,
            "sources": sources,
            "warnings": warnings,
            "missing_information": missing_information,
            "follow_up_required": follow_up_required,
            "safety_assessment": safety_assessment,
            "reasoning_graph_ref": reasoning_graph_ref,
        }
