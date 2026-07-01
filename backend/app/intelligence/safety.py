from typing import Any

from app.schemas.evidence import BaseEvidence
from pydantic import BaseModel, Field


class SafetyAssessment(BaseModel):
    """
    Structured response details representing the safety check outcomes.
    """
    is_safe: bool = Field(..., description="True if the recommendation is cleared for output.")
    risk_score: float = Field(..., description="Calculated safety risk score (0.0 to 1.0).")
    flagged_reasons: list[str] = Field(default_factory=list, description="Reasoning segments for safety flags.")
    warnings: list[str] = Field(default_factory=list, description="Safety warnings passed to the client.")
    safety_metrics: dict[str, Any] = Field(default_factory=dict, description="Metrics summarizing checks run.")

class SafetyGuard:
    """
    Monitors agent result collections for hallucination risks, contradictions, and data gaps.
    """
    def __init__(self, confidence_threshold: float = 0.5) -> None:
        self.confidence_threshold = confidence_threshold

    def assess(
        self,
        evidence_list: list[BaseEvidence],
        overall_confidence: float
    ) -> SafetyAssessment:
        reasons: list[str] = []
        warnings: list[str] = []
        risk_score = 0.0

        # 1. Check Low Confidence threshold
        if overall_confidence < self.confidence_threshold:
            reasons.append("Overall confidence score falls below safety threshold.")
            risk_score += 0.4

        # 2. Check Contradictory evidence indicators
        invalid_items = [ev for ev in evidence_list if ev.validation_state == "invalid"]
        if invalid_items:
            reasons.append(f"Flagged invalid evidence segments returned by: {list({e.agent for e in invalid_items})}")
            risk_score += 0.3

        # 3. Check low confidence inputs count
        low_conf_items = [ev for ev in evidence_list if ev.confidence < 0.4]
        if low_conf_items:
            warnings.append(f"Recommendation contains low-confidence inputs from: {list({e.agent for e in low_conf_items})}")
            risk_score += 0.15

        # 4. Check Empty Evidence list
        if not evidence_list:
            reasons.append("No active evidence statements returned for validation check.")
            risk_score = 1.0

        # Cap risk score at 1.0
        risk_score = min(risk_score, 1.0)
        is_safe = len(reasons) == 0

        return SafetyAssessment(
            is_safe=is_safe,
            risk_score=risk_score,
            flagged_reasons=reasons,
            warnings=warnings,
            safety_metrics={
                "total_checks_run": 4,
                "evidence_count_assessed": len(evidence_list),
                "low_confidence_sources_count": len(low_conf_items),
                "invalid_sources_count": len(invalid_items)
            }
        )
