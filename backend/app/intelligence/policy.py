import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.schemas.responses import TrustedRecommendation
from pydantic import BaseModel, Field


class Policy(BaseModel):
    """
    AI Policy specification for recommendation validation.
    """
    policy_id: str = Field(..., description="Unique policy identifier.")
    version: str = Field(..., description="Semantic version representation.")
    description: str = Field(..., description="Policy description details.")
    enabled: bool = Field(default=True, description="Flag indicating if the policy is active.")
    region_scope: Optional[str] = Field(default=None, description="Applies only to this region location.")
    crop_scope: Optional[str] = Field(default=None, description="Applies only to this target crop.")
    min_confidence: float = Field(default=0.0, description="Minimum acceptable confidence threshold.")
    forbidden_terms: list[str] = Field(default_factory=list, description="Prohibited keyword warnings list.")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata placeholder properties.")


class PolicyEvaluationReport(BaseModel):
    """
    Evaluation output report capturing verification outcomes.
    """
    evaluation_id: str = Field(..., description="Evaluation instance identifier.")
    policy_id: str = Field(..., description="Target policy identifier.")
    version: str = Field(..., description="Version of the evaluated policy.")
    passed: bool = Field(..., description="Boolean indicating if all checks passed.")
    violations: list[str] = Field(default_factory=list, description="Captured list of policy violations.")
    timestamp: float = Field(default_factory=time.time, description="Creation epoch timestamp.")


class PolicyEngine:
    """
    Registry and evaluation engine coordinating recommendation policies.
    """
    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._load_default_policies()

    def register(self, policy: Policy) -> None:
        """
        Registers a new policy into the engine directory.
        """
        self._policies[policy.policy_id] = policy

    def discover(self, policy_id: str) -> Optional[Policy]:
        """
        Looks up a registered policy by ID.
        """
        return self._policies.get(policy_id)

    def list_policies(self) -> list[Policy]:
        """
        Returns all registered policies.
        """
        return list(self._policies.values())

    async def evaluate(
        self,
        recommendation: TrustedRecommendation,
        context: AgentContext
    ) -> list[PolicyEvaluationReport]:
        """
        Verifies a TrustedRecommendation against all active and scoped policies.
        """
        reports: list[PolicyEvaluationReport] = []

        for policy in self._policies.values():
            if not policy.enabled:
                continue

            # Scope checks: verify location
            if policy.region_scope and context.location:
                if policy.region_scope.lower() not in context.location.lower():
                    continue

            # Scope checks: verify crop
            if policy.crop_scope and context.crop:
                if policy.crop_scope.lower() not in context.crop.lower():
                    continue

            violations: list[str] = []

            # 1. Confidence threshold validation
            if recommendation.confidence < policy.min_confidence:
                violations.append(
                    f"Recommendation confidence {recommendation.confidence} "
                    f"below minimum required {policy.min_confidence} for policy '{policy.policy_id}'."
                )

            # 2. Forbidden terms validation (safety assessment scan)
            recommendation_text = (recommendation.recommendation + " " + recommendation.summary).lower()
            for term in policy.forbidden_terms:
                if term.lower() in recommendation_text:
                    violations.append(
                        f"Forbidden term '{term}' detected under policy '{policy.policy_id}'."
                    )

            import uuid
            report = PolicyEvaluationReport(
                evaluation_id=f"EVR-{str(uuid.uuid4())[:8]}",
                policy_id=policy.policy_id,
                version=policy.version,
                passed=len(violations) == 0,
                violations=violations
            )
            reports.append(report)

        return reports

    def _load_default_policies(self) -> None:
        """
        Loads base framework policies (threshold and safety checks).
        """
        # Default safety policy
        self.register(Policy(
            policy_id="default-safety-policy",
            version="1.0.0",
            description="Default agricultural safety checks policy.",
            min_confidence=0.5,
            forbidden_terms=["unapproved chemical", "illegal pesticide", "banned poison"]
        ))

        # Region-specific placeholder example
        self.register(Policy(
            policy_id="punjab-water-policy",
            version="1.0.0",
            description="Water conservation guidance for Punjab farming.",
            region_scope="Punjab",
            min_confidence=0.6,
            forbidden_terms=["excessive flooding", "unrestricted borewell"]
        ))
