import logging
from typing import List

from pydantic import BaseModel

logger = logging.getLogger("kisan_mitra_ai.governance.rules")

class RuleResult(BaseModel):
    rule_name: str
    rule_type: str  # pre_execution | post_execution | validation | safety | escalation
    passed: bool
    message: str

class RuleEngine:
    """
    Enforces pre/post execution checks, validation constraints, safety gates, and escalation conditions.
    """
    def __init__(self) -> None:
        pass

    def evaluate_pre_execution_rules(self, query: str) -> List[RuleResult]:
        """
        Enforces sanity and safety boundaries before passing query to the LLM orchestrator.
        """
        results: List[RuleResult] = []

        # Rule 1: Length check
        if len(query) < 3:
            results.append(RuleResult(
                rule_name="Minimum Length check",
                rule_type="pre_execution",
                passed=False,
                message="Query prompt is too short to process."
            ))
        else:
            results.append(RuleResult(
                rule_name="Minimum Length check",
                rule_type="pre_execution",
                passed=True,
                message="Query length meets requirements."
            ))

        # Rule 2: SQL Injection / Destructive Pattern Safety check
        lower_q = query.lower()
        destructive_tokens = ["drop table", "delete from", "select * from information_schema"]
        contains_destructive = any(token in lower_q for token in destructive_tokens)
        if contains_destructive:
            results.append(RuleResult(
                rule_name="Destructive command safety",
                rule_type="safety",
                passed=False,
                message="Query contains forbidden destructive command patterns."
            ))
        else:
            results.append(RuleResult(
                rule_name="Destructive command safety",
                rule_type="safety",
                passed=True,
                message="No destructive SQL commands detected."
            ))

        return results

    def evaluate_post_execution_rules(
        self,
        response_text: str,
        confidence: float,
        risk_score: float = 0.0
    ) -> List[RuleResult]:
        """
        Validates the output advisory parameters, confidence scores, and safety ratings.
        """
        results: List[RuleResult] = []

        # Rule 1: Response Completeness validation
        if not response_text or len(response_text) < 10:
            results.append(RuleResult(
                rule_name="Response completeness",
                rule_type="validation",
                passed=False,
                message="Response is incomplete or empty."
            ))
        else:
            results.append(RuleResult(
                rule_name="Response completeness",
                rule_type="validation",
                passed=True,
                message="Advisory response is populated."
            ))

        # Rule 2: Confidence & Risk Escalation rule
        if confidence < 0.5 or risk_score > 0.8:
            results.append(RuleResult(
                rule_name="Human Escalation check",
                rule_type="escalation",
                passed=False,
                message="Low confidence or high risk score triggers mandatory human intervention."
            ))
        else:
            results.append(RuleResult(
                rule_name="Human Escalation check",
                rule_type="escalation",
                passed=True,
                message="Confidence and risk are within nominal operational parameters."
            ))

        return results
