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

        # Extract crop/commodity and location dynamically from query or context
        crop = context.crop
        location = context.location
        if request and request.query:
            q_lower = request.query.lower()
            crops = ["wheat", "rice", "paddy", "tomato", "cotton", "maize", "mustard", "potato", "onion", "chilli", "sugarcane"]
            locations = ["ludhiana", "khanna", "punjab", "karnataka", "kolar", "hubballi", "haryana", "delhi", "patna"]
            for c in crops:
                if c in q_lower:
                    crop = c.title()
                    break
            for l in locations:
                if l in q_lower:
                    location = l.title()
                    break

        crop = crop or "Wheat"
        location = location or "Punjab"
        market_data = await self.market_service.get_market_prices(crop, location, context)

        # Parse price dynamically from market_data if available
        import re
        modal_price = 2275.0
        price_match = re.search(r"₹?\s*(\d{3,5})", market_data)
        if price_match:
            modal_price = float(price_match.group(1))

        # Formulate structured MarketEvidence
        evidence = MarketEvidence(
            id=f"ev-market-{context.request_id}",
            source="MandiPriceService",
            agent=self.name,
            confidence=0.95,
            weight=0.8,
            reasoning=f"Mandi price report for {crop} in {location}: {market_data}",
            commodity=crop,
            modal_price=modal_price,
            market_name=f"{location} APMC Mandi",
            ontology_references=[crop.lower(), "market_price"]
        )

        content = f"Mandi price report for {crop} in {location}: {market_data}"

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content,
            confidence=0.95,
            metrics={"latency_ms": self.state.execution_time},
            logs=[f"Consulted mandi price registry for {crop} in {location}."],
            evidence=[evidence.model_dump()]
        )


    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return "price" in response.content.lower()

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
