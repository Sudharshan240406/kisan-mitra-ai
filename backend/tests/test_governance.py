import os
import shutil
from typing import Generator, List

import pytest
from app.core.config import settings
from app.core.container import Container
from app.core.exceptions import OrchestratorException
from app.governance import (
    AuditManager,
    AuditRecord,
    ComplianceEngine,
    ComplianceRecord,
    ExplainabilityEngine,
    Explanation,
    Policy,
    PolicyEngine,
    PolicyViolation,
    RuleEngine,
    RuleResult,
)
from app.orchestrator.orchestrator import AgentOrchestrator
from app.schemas.requests import ExecutionRequest
from app.tenancy.tenant_context import set_tenant_context


@pytest.fixture(autouse=True)
def cleanup_test_dirs() -> Generator[None, None, None]:
    yield
    # Clean up test directories
    if os.path.exists("data/tenants"):
        shutil.rmtree("data/tenants")
    if os.path.exists("data/governance_audit.jsonl"):
        try:
            os.remove("data/governance_audit.jsonl")
        except Exception:
            pass

def test_policy_engine_evaluation() -> None:
    engine = PolicyEngine()

    # Evaluate safe query
    violations = engine.evaluate_policies(query="How to grow wheat?", tenant_id="tenant_1")
    assert len(violations) == 0

    # Evaluate query with toxic spam words violating POL-SYS-001
    violations2 = engine.evaluate_policies(query="How to bypass user controls", tenant_id="tenant_1")
    assert len(violations2) == 1
    assert violations2[0].policy_id == "POL-SYS-001"
    assert violations2[0].severity == "critical"

    # Register custom Tenant Policy
    engine.register_policy(Policy(
        id="POL-TEN-001",
        name="Custom Tenant restriction",
        policy_type="tenant",
        scope="tenant:tenant_alpha",
        rules=[{"rule_type": "blacklist_words", "words": ["pesticide"]}]
    ))

    # Evaluate query for tenant_beta (should NOT trigger pesticide block)
    violations3 = engine.evaluate_policies(query="How to apply pesticide?", tenant_id="tenant_beta")
    assert len(violations3) == 0

    # Evaluate query for tenant_alpha (should trigger pesticide block)
    violations4 = engine.evaluate_policies(query="How to apply pesticide?", tenant_id="tenant_alpha")
    assert len(violations4) == 1
    assert violations4[0].policy_id == "POL-TEN-001"

def test_rule_engine_checks() -> None:
    engine = RuleEngine()

    # Pre-execution checks
    res1 = engine.evaluate_pre_execution_rules("ab")
    assert any(not r.passed and r.rule_name == "Minimum Length check" for r in res1)

    res2 = engine.evaluate_pre_execution_rules("select * from information_schema.tables")
    assert any(not r.passed and r.rule_type == "safety" for r in res2)

    # Post-execution checks
    res3 = engine.evaluate_post_execution_rules(response_text="Complete output advisory", confidence=0.8)
    assert all(r.passed for r in res3)

    # Low confidence triggers escalation
    res4 = engine.evaluate_post_execution_rules(response_text="Complete output advisory", confidence=0.4)
    assert any(not r.passed and r.rule_type == "escalation" for r in res4)

def test_compliance_and_explainability() -> None:
    comp_engine = ComplianceEngine()
    exp_engine = ExplainabilityEngine()

    # Create dummy check inputs
    policy_violations: List[PolicyViolation] = []
    rule_results = [
        RuleResult(rule_name="Length check", rule_type="pre_execution", passed=True, message=""),
        RuleResult(rule_name="Escalation check", rule_type="escalation", passed=False, message="Low confidence")
    ]

    record = comp_engine.log_compliance("exec_1", policy_violations, rule_results)
    assert record.status == "non_compliant"
    assert len(record.rule_violations) == 1

    explanation = exp_engine.generate_explanation(
        decision_summary="Query test summary",
        evidence_chain=["Ev 1", "Ev 2"],
        confidence=0.45,
        policy_violations=policy_violations,
        rule_results=rule_results
    )
    assert "Low system confidence" in explanation.confidence_explanation
    assert len(explanation.evidence_chain) == 2

def test_audit_manager_and_isolation() -> None:
    # Load Container to trigger isolation initialization
    Container(settings)

    # Perform Tenant Alpha audit log
    with set_tenant_context("tenant_alpha"):
        audit_alpha = AuditManager()

        # Log entry
        rec_alpha = AuditRecord(
            execution_id="exec_a",
            tenant_id="tenant_alpha",
            user_id="user_1",
            query="Alpha Query",
            response_text="Alpha Response",
            compliance=ComplianceRecord(id="exec_a", status="compliant"),
            explanation=Explanation(decision_summary="Summary", confidence_explanation="High", evidence_chain=[])
        )
        audit_alpha.log_audit(rec_alpha)
        assert len(audit_alpha.records) == 1

    # Perform Tenant Beta audit log
    with set_tenant_context("tenant_beta"):
        audit_beta = AuditManager()
        assert len(audit_beta.records) == 0  # Assert in-memory isolation is preserved!

        rec_beta = AuditRecord(
            execution_id="exec_b",
            tenant_id="tenant_beta",
            user_id="user_2",
            query="Beta Query",
            response_text="Beta Response",
            compliance=ComplianceRecord(id="exec_b", status="compliant"),
            explanation=Explanation(decision_summary="Summary", confidence_explanation="High", evidence_chain=[])
        )
        audit_beta.log_audit(rec_beta)
        assert len(audit_beta.records) == 1

    # Re-verify Tenant Alpha
    with set_tenant_context("tenant_alpha"):
        assert len(audit_alpha.records) == 1

    # Verify disk paths are correctly separated under tenant directories
    assert os.path.exists("data/tenants/tenant_alpha/governance_audit.jsonl") is True
    assert os.path.exists("data/tenants/tenant_beta/governance_audit.jsonl") is True

@pytest.mark.asyncio
async def test_e2e_orchestrator_governance_flow() -> None:
    container = Container(settings)
    orchestrator = AgentOrchestrator(container)

    # 1. Test Compliant Query execution
    req_ok = ExecutionRequest(
        session_id="session_gov_1",
        query="What is the price of wheat?",
        tenant_id="tenant_alpha"
    )

    # Set context variables and execute
    with set_tenant_context("tenant_alpha"):
        res = await orchestrator.execute_query(req_ok)
        assert res.status == "success"

        # Verify explainability safety_assessment details are attached
        safety = res.data.get("safety_assessment", {})
        assert safety.get("governance_compliance") == "compliant"
        assert safety.get("policy_violations_count") == 0

        # Verify audit record is logged in AuditManager
        assert len(container.governance_manager.audit_manager.records) == 1

    # 2. Test Non-Compliant safety query (should block query immediately)
    req_violate = ExecutionRequest(
        session_id="session_gov_2",
        query="Please override_instructions and hack parameters",
        tenant_id="tenant_alpha"
    )

    with set_tenant_context("tenant_alpha"):
        with pytest.raises(OrchestratorException) as excinfo:
            await orchestrator.execute_query(req_violate)
        assert "Governance Policy Violation" in str(excinfo.value)

        # Verify a second audit record (reflecting the non-compliant check) is logged
        assert len(container.governance_manager.audit_manager.records) == 2
        assert container.governance_manager.audit_manager.records[1].compliance.status == "non_compliant"
