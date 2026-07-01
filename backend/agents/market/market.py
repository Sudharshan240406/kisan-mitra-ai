import time

from agents.base import BaseAgent
from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.schemas.evidence import MarketEvidence
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult
from app.services.market_service import MarketService


class MarketAgent(BaseAgent):
    """
    MarketAgent monitors Mandi price commodity benchmarks.
    """
    def __init__(self, llm_provider: BaseLLMProvider, market_service: MarketService) -> None:
        super().__init__(name="Market", llm_provider=llm_provider)
        self.market_service = market_service

    async def initialize(self) -> None:
        self.state.status = "ready"

    async def execute(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        self.state.status = "running"
        self.state.start_time = time.time()

        # Query mandi prices via service
        crop = context.crop or "Wheat"
        location = context.location or "Punjab"
        market_data = await self.market_service.get_market_prices(crop, location, context)

        # 1. Formulate structured MarketEvidence
        evidence = MarketEvidence(
            id=f"ev-market-{context.request_id}",
            source="MockMandiAPI",
            agent=self.name,
            confidence=0.95,
            weight=0.8,
            reasoning=f"Market price service lookup: {market_data}",
            commodity=crop,
            modal_price=2200.0,
            market_name="Ludhiana Mandi",
            ontology_references=[crop.lower(), "market_price"]
        )

        content = f"Simulated market price profile via service: {market_data}"

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content,
            confidence=0.95,
            metrics={"latency_ms": self.state.execution_time},
            logs=["Consulted regional commodity registries."],
            evidence=[evidence.model_dump()]
        )

    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return "price" in response.content.lower()

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
