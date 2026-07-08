import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Policy(BaseModel):
    id: str
    name: str
    policy_type: str  # system | organization | tenant | model | prompt | response
    scope: str        # e.g., '*', 'tenant:tenant_alpha', 'org:org_beta'
    rules: List[Dict[str, Any]] = Field(default_factory=list)
    active: bool = True
    created_at: float = Field(default_factory=time.time)

class PolicyViolation(BaseModel):
    policy_id: str
    policy_type: str
    message: str
    severity: str  # info | warning | critical

class PolicyEngine:
    """
    Enforces compliance against System, Organization, Tenant, Model, Prompt, and Response policies.
    """
    def __init__(self) -> None:
        self.policies: Dict[str, Policy] = {}
        self._load_default_policies()

    def register_policy(self, policy: Policy) -> None:
        self.policies[policy.id] = policy

    def get_policies_by_type(self, policy_type: str) -> List[Policy]:
        return [p for p in self.policies.values() if p.active and p.policy_type == policy_type]

    def _load_default_policies(self) -> None:
        # Default System Policy checking for query spam
        self.register_policy(Policy(
            id="POL-SYS-001",
            name="Default Query Safety",
            policy_type="system",
            scope="*",
            rules=[{"rule_type": "blacklist_words", "words": ["hack", "bypass", "override_instructions"]}]
        ))
        # Default Model Usage Policy
        self.register_policy(Policy(
            id="POL-MDL-001",
            name="Allowed Models Usage",
            policy_type="model",
            scope="*",
            rules=[{"rule_type": "approved_models", "models": ["llama3", "gpt-4", "mock"]}]
        ))

    def _check_text_rules(self, policy: Policy, query: str) -> List[PolicyViolation]:
        violations: List[PolicyViolation] = []
        for rule in policy.rules:
            if rule.get("rule_type") == "blacklist_words":
                for word in rule.get("words", []):
                    if word.lower() in query.lower():
                        violations.append(PolicyViolation(
                            policy_id=policy.id,
                            policy_type=policy.policy_type,
                            message=f"Query contains blacklisted keyword '{word}'",
                            severity="critical"
                        ))
        return violations

    def _check_model_rules(self, policy: Policy, model_id: str) -> List[PolicyViolation]:
        violations: List[PolicyViolation] = []
        for rule in policy.rules:
            if rule.get("rule_type") == "approved_models":
                if model_id not in rule.get("models", []):
                    violations.append(PolicyViolation(
                        policy_id=policy.id,
                        policy_type="model",
                        message=f"Model '{model_id}' is not approved for execution.",
                        severity="critical"
                    ))
        return violations

    def evaluate_policies(
        self,
        query: str,
        tenant_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> List[PolicyViolation]:
        """
        Validates the incoming query and parameters against all active system/tenant/org/model policies.
        """
        violations: List[PolicyViolation] = []

        # Determine scopes that apply to this execution context
        applicable_scopes = {"*"}
        if tenant_id:
            applicable_scopes.add(f"tenant:{tenant_id}")
        if organization_id:
            applicable_scopes.add(f"org:{organization_id}")

        for policy in self.policies.values():
            if not policy.active or policy.scope not in applicable_scopes:
                continue

            # Run specific checks
            if policy.policy_type in {"system", "tenant", "organization"}:
                violations.extend(self._check_text_rules(policy, query))

            if policy.policy_type == "model" and model_id:
                violations.extend(self._check_model_rules(policy, model_id))

        return violations
