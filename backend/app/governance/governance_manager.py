import time
from typing import Any, Dict, List, Optional

from .audit_manager import AuditManager, AuditRecord
from .compliance_engine import ComplianceEngine
from .explainability_engine import ExplainabilityEngine
from .policy_engine import PolicyEngine
from .rule_engine import RuleEngine


class GovernanceManager:
    """
    Unified manager orchestrating policy check, rule evaluations, compliance logs,
    explainability traces, and audit ledger recordings.
    """
    def __init__(self, container: Any = None) -> None:
        self.container = container
        self.policy_engine = PolicyEngine()
        self.rule_engine = RuleEngine()
        self.compliance_engine = ComplianceEngine()
        self.explainability_engine = ExplainabilityEngine()
        self.audit_manager = AuditManager()

    def run_pre_execution_checks(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Runs pre-execution safety rules and policy checks.
        """
        policy_violations = self.policy_engine.evaluate_policies(
            query=query,
            tenant_id=tenant_id,
            organization_id=organization_id,
            model_id=model_id
        )
        rule_results = self.rule_engine.evaluate_pre_execution_rules(query)

        has_critical_violation = any(v.severity == "critical" for v in policy_violations)
        has_failed_rule = any(not r.passed and r.rule_type in ("safety", "pre_execution") for r in rule_results)

        return {
            "passed": not (has_critical_violation or has_failed_rule),
            "policy_violations": policy_violations,
            "rule_results": rule_results
        }

    def run_post_execution_checks(
        self,
        execution_id: str,
        query: str,
        response_text: str,
        confidence: float,
        pre_checks: Dict[str, Any],
        user_id: str = "anonymous",
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        model_id: Optional[str] = None,
        risk_score: float = 0.0,
        evidence_chain: Optional[List[str]] = None
    ) -> AuditRecord:
        """
        Evaluates post-execution validation, compliance tracking, explainability compilation, and audit ledger logs.
        """
        # 1. Run post-execution rules
        post_rules = self.rule_engine.evaluate_post_execution_rules(
            response_text=response_text,
            confidence=confidence,
            risk_score=risk_score
        )
        all_rules = pre_checks["rule_results"] + post_rules

        # 2. Check compliance
        compliance_record = self.compliance_engine.log_compliance(
            execution_id=execution_id,
            policy_violations=pre_checks["policy_violations"],
            rule_results=all_rules,
            model_id=model_id
        )

        # 3. Compile explanation
        explanation = self.explainability_engine.generate_explanation(
            decision_summary=f"Synthesized response for query: {query}",
            evidence_chain=evidence_chain or [],
            confidence=confidence,
            policy_violations=pre_checks["policy_violations"],
            rule_results=all_rules
        )

        # 4. Write audit record
        audit_rec = AuditRecord(
            execution_id=execution_id,
            tenant_id=tenant_id,
            organization_id=organization_id,
            timestamp=time.time(),
            user_id=user_id,
            query=query,
            response_text=response_text,
            policy_violations=pre_checks["policy_violations"],
            rule_results=all_rules,
            compliance=compliance_record,
            explanation=explanation
        )
        self.audit_manager.log_audit(audit_rec)
        return audit_rec
