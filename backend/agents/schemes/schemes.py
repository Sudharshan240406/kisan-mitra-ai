import time

from agents.base import BaseAgent
from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.schemas.evidence import GovernmentSchemeEvidence
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult
from app.services.scheme_service import GovernmentSchemeService


class GovernmentSchemeAgent(BaseAgent):
    """
    GovernmentSchemeAgent matches farmers with welfare policies.
    """
    def __init__(self, llm_provider: BaseLLMProvider, scheme_service: GovernmentSchemeService) -> None:
        super().__init__(name="GovernmentScheme", llm_provider=llm_provider)
        self.scheme_service = scheme_service

    async def initialize(self) -> None:
        self.state.status = "ready"

    async def execute(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        self.state.status = "running"
        self.state.start_time = time.time()

        # Query schemes via service
        farmer_id = context.farmer_id or "FR-101"
        scheme_data = await self.scheme_service.get_schemes_eligibility(farmer_id, context)

        # 1. Formulate structured GovernmentSchemeEvidence
        evidence = GovernmentSchemeEvidence(
            id=f"ev-scheme-{context.request_id}",
            source="SubsidyPortalAPI",
            agent=self.name,
            confidence=0.92,
            weight=0.7,
            reasoning=f"Scheme service lookup: {scheme_data}",
            scheme_title="PM-KISAN",
            eligibility_matched=True,
            ontology_references=["subsidy_scheme"]
        )

        content = f"Simulated welfare query via service: {scheme_data}"

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content,
            confidence=0.92,
            metrics={"latency_ms": self.state.execution_time},
            logs=["Consulted government scheme registries."],
            evidence=[evidence.model_dump()]
        )

    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return len(response.content) > 0

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
