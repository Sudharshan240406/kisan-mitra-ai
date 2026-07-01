import time

from agents.base import BaseAgent
from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.schemas.evidence import KnowledgeEvidence
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult
from app.services.knowledge_service import KnowledgeService


class KnowledgeAgent(BaseAgent):
    """
    KnowledgeAgent query agricultural reference manuals and pathology diagnostics.
    """
    def __init__(self, llm_provider: BaseLLMProvider, knowledge_service: KnowledgeService) -> None:
        super().__init__(name="Knowledge", llm_provider=llm_provider)
        self.knowledge_service = knowledge_service

    async def initialize(self) -> None:
        self.state.status = "ready"

    async def execute(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        self.state.status = "running"
        self.state.start_time = time.time()

        # Query pathology manuals via service
        crop = context.crop or "Wheat"
        symptoms = context.metadata.get("symptoms") or ["yellow leaves"]
        knowledge_data = await self.knowledge_service.get_pathology_advisory(crop, symptoms, context)

        # 1. Formulate structured KnowledgeEvidence
        evidence = KnowledgeEvidence(
            id=f"ev-knowledge-{context.request_id}",
            source="CropPathologyManuals",
            agent=self.name,
            confidence=0.88,
            weight=0.9,
            reasoning=f"Knowledge service lookup: {knowledge_data}",
            citation="Crop Manual Page 45",
            document_title="Wheat Disease Diagnostics",
            ontology_references=[crop.lower(), "rust"]
        )

        content = f"Simulated knowledge search via service: {knowledge_data}"

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content,
            confidence=0.88,
            metrics={"latency_ms": self.state.execution_time},
            logs=["Scanned crop disease manuals."],
            evidence=[evidence.model_dump()]
        )

    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return True

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
