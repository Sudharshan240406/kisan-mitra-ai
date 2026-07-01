import time

from agents.base import BaseAgent
from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.schemas.evidence import WeatherEvidence
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult
from app.services.weather_service import WeatherService


class WeatherAgent(BaseAgent):
    """
    WeatherAgent coordinates meteorological parameter advisory reviews.
    """
    def __init__(self, llm_provider: BaseLLMProvider, weather_service: WeatherService) -> None:
        super().__init__(name="Weather", llm_provider=llm_provider)
        self.weather_service = weather_service

    async def initialize(self) -> None:
        self.state.status = "ready"

    async def execute(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        self.state.status = "running"
        self.state.start_time = time.time()

        # Call the weather service
        location = context.location or "Punjab"
        weather_data = await self.weather_service.get_weather_forecast(location, context)

        # 1. Formulate structured WeatherEvidence
        evidence = WeatherEvidence(
            id=f"ev-weather-{context.request_id}",
            source="MockWeatherAPI",
            agent=self.name,
            confidence=0.9,
            weight=1.0,
            reasoning=f"Weather service lookup: {weather_data}",
            temperature=30.0,
            rainfall=15.0,
            humidity=75.0,
            ontology_references=["weather_forecast"]
        )

        content = f"Simulated weather forecast via service: {weather_data}"

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content,
            confidence=0.9,
            metrics={"latency_ms": self.state.execution_time},
            logs=["Fetched weather forecast registry index."],
            evidence=[evidence.model_dump()]
        )

    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return len(response.content) > 0

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
