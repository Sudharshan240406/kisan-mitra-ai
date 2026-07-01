import time

from agents.base import BaseAgent
from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.schemas.evidence import MemoryEvidence
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult
from app.services.memory_service import MemoryService


class MemoryAgent(BaseAgent):
    """
    MemoryAgent tracks session contextual flags and historic logs.
    """
    def __init__(self, llm_provider: BaseLLMProvider, memory_service: MemoryService) -> None:
        super().__init__(name="Memory", llm_provider=llm_provider)
        self.memory_service = memory_service

    async def initialize(self) -> None:
        self.state.status = "ready"

    async def execute(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        self.state.status = "running"
        self.state.start_time = time.time()

        # Query memory history via service
        farmer_id = context.farmer_id or "FR-101"
        memory_data = await self.memory_service.get_farmer_history(farmer_id, context)

        # 1. Formulate structured MemoryEvidence
        evidence = MemoryEvidence(
            id=f"ev-memory-{context.request_id}",
            source="ARM",
            agent=self.name,
            confidence=1.0,
            weight=1.0,
            reasoning=f"Memory service lookup: {memory_data}",
            farmer_id=farmer_id,
            historical_patterns=["Wheat farming", "Rabi season matching"],
            ontology_references=["farmer_profile"]
        )

        content = f"Simulated memory fetch via service: {memory_data}"

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content,
            confidence=1.0,
            metrics={"latency_ms": self.state.execution_time},
            logs=["Retrieved memory vectors."],
            evidence=[evidence.model_dump()]
        )

    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return True

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
