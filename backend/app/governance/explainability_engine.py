from typing import List

from pydantic import BaseModel, Field

from .policy_engine import PolicyViolation
from .rule_engine import RuleResult


class Explanation(BaseModel):
    decision_summary: str
    evidence_chain: List[str] = Field(default_factory=list)
    confidence_explanation: str
    policy_evaluation_results: List[PolicyViolation] = Field(default_factory=list)
    rule_evaluation_history: List[RuleResult] = Field(default_factory=list)

class ExplainabilityEngine:
    """
    Constructs comprehensive human-readable explanations trace maps for LLM and specialist choices.
    """
    def __init__(self) -> None:
        pass

    def generate_explanation(
        self,
        decision_summary: str,
        evidence_chain: List[str],
        confidence: float,
        policy_violations: List[PolicyViolation],
        rule_results: List[RuleResult]
    ) -> Explanation:
        """
        Synthesizes an explainable report highlighting decision roots, safety flags, and confidence weights.
        """
        if confidence >= 0.8:
            conf_msg = f"High system confidence of {confidence:.2f} based on dense vector matches and verified specialist outputs."
        elif confidence >= 0.5:
            conf_msg = f"Nominal system confidence of {confidence:.2f} with regular evidence confirmations."
        else:
            conf_msg = f"Low system confidence of {confidence:.2f}. Recommended human operator confirmation."

        return Explanation(
            decision_summary=decision_summary,
            evidence_chain=evidence_chain,
            confidence_explanation=conf_msg,
            policy_evaluation_results=policy_violations,
            rule_evaluation_history=rule_results
        )
