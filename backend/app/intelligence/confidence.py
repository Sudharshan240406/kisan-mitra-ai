
from app.schemas.evidence import BaseEvidence
from pydantic import BaseModel, Field


class ConfidenceReport(BaseModel):
    """
    Standard confidence report summarizing statistical agent and evidence metrics.
    """
    agent_confidences: dict[str, float] = Field(..., description="Individual agent confidence scores mapping.")
    evidence_weights: dict[str, float] = Field(..., description="Weight parameter values per evidence ID.")
    decision_confidence: float = Field(..., description="Un-penalized decision strategy confidence.")
    overall_confidence: float = Field(..., description="Net confidence score after applying missing parameter penalties.")
    missing_penalty: float = Field(..., description="Penalty deducted for missing query inputs.")

class ConfidenceAggregator:
    """
    Aggregates evidence metrics and applies location/crop data gaps penalties.
    """
    def __init__(self, penalty_per_missing: float = 0.15) -> None:
        self.penalty_per_missing = penalty_per_missing

    def calculate_confidence(
        self,
        evidence_list: list[BaseEvidence],
        missing_fields: list[str]
    ) -> ConfidenceReport:
        agent_confs = {}
        ev_weights = {}

        weighted_sum = 0.0
        total_weight = 0.0

        for ev in evidence_list:
            agent_confs[ev.agent] = ev.confidence
            ev_weights[ev.id] = ev.weight

            weighted_sum += ev.confidence * ev.weight
            total_weight += ev.weight

        # Calculate raw decision confidence
        decision_conf = (weighted_sum / total_weight) if total_weight > 0.0 else 1.0

        # Calculate penalty for missing information parameters
        penalty = len(missing_fields) * self.penalty_per_missing

        # Calculate net penalized overall confidence
        overall_conf = max(decision_conf - penalty, 0.0)

        return ConfidenceReport(
            agent_confidences=agent_confs,
            evidence_weights=ev_weights,
            decision_confidence=decision_conf,
            overall_confidence=overall_conf,
            missing_penalty=penalty
        )
