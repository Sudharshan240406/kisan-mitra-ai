import logging
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .policy_engine import PolicyViolation
from .rule_engine import RuleResult

logger = logging.getLogger("kisan_mitra_ai.governance.compliance")

class ComplianceRecord(BaseModel):
    id: str
    status: str  # compliant | non_compliant
    policy_violations: List[PolicyViolation] = Field(default_factory=list)
    rule_violations: List[RuleResult] = Field(default_factory=list)
    sensitive_operations: List[str] = Field(default_factory=list)
    restricted_data_accessed: List[str] = Field(default_factory=list)
    model_compliant: bool = True

class ComplianceEngine:
    """
    Maintains and audits the compliance posture of executed user requests.
    """
    def __init__(self) -> None:
        self.records: Dict[str, ComplianceRecord] = {}

    def log_compliance(
        self,
        execution_id: str,
        policy_violations: List[PolicyViolation],
        rule_results: List[RuleResult],
        sensitive_ops: Optional[List[str]] = None,
        restricted_accesses: Optional[List[str]] = None,
        model_id: Optional[str] = None
    ) -> ComplianceRecord:
        """
        Creates and logs a compliance assessment.
        """
        rule_violations = [r for r in rule_results if not r.passed]

        has_violations = len(policy_violations) > 0 or len(rule_violations) > 0
        status = "non_compliant" if has_violations else "compliant"

        # Check model usage compliance (is the model approved in policy violations?)
        model_compliant = not any(v.policy_type == "model" for v in policy_violations)

        record = ComplianceRecord(
            id=execution_id,
            status=status,
            policy_violations=policy_violations,
            rule_violations=rule_violations,
            sensitive_operations=sensitive_ops or [],
            restricted_data_accessed=restricted_accesses or [],
            model_compliant=model_compliant
        )
        self.records[execution_id] = record

        if status == "non_compliant":
            logger.warning(f"Compliance Violation detected for Execution '{execution_id}': status={status}")
        else:
            logger.info(f"Compliance Check Passed for Execution '{execution_id}'")

        return record

    def get_compliance_record(self, execution_id: str) -> Optional[ComplianceRecord]:
        return self.records.get(execution_id)
