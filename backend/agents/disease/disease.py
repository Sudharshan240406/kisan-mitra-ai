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

        # Extract crop and symptoms dynamically from query or context
        crop = context.crop
        symptoms = list(context.metadata.get("symptoms") or [])
        if request and request.query:
            q_lower = request.query.lower()
            crops = ["wheat", "rice", "paddy", "tomato", "cotton", "maize", "mustard", "potato", "onion", "chilli", "sugarcane"]
            for c in crops:
                if c in q_lower:
                    crop = c.title()
                    break
            
            symptom_keywords = ["brown spots", "yellow leaves", "rust", "pustules", "blight", "spots", "wilt", "rot"]
            for s in symptom_keywords:
                if s in q_lower and s not in symptoms:
                    symptoms.append(s)

        crop = crop or "Wheat"
        symptoms = symptoms or ["yellow leaves"]
        knowledge_data = await self.knowledge_service.get_pathology_advisory(crop, symptoms, context)

        # Formulate structured KnowledgeEvidence
        evidence = KnowledgeEvidence(
            id=f"ev-knowledge-{context.request_id}",
            source="CropPathologyManuals",
            agent=self.name,
            confidence=0.88,
            weight=0.9,
            reasoning=f"Pathology advisory for {crop} ({', '.join(symptoms)}): {knowledge_data}",
            citation=f"{crop} Disease Guide",
            document_title=f"{crop} Pathology Manual",
            ontology_references=[crop.lower()]
        )

        content = f"Pathology advisory for {crop} ({', '.join(symptoms)}): {knowledge_data}"

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content,
            confidence=0.88,
            metrics={"latency_ms": self.state.execution_time},
            logs=[f"Scanned pathology manuals for {crop} with symptoms {symptoms}."],
            evidence=[evidence.model_dump()]
        )


    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return True

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
