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

        # Extract location from query if available, fallback to context or default
        location = context.location
        if request and request.query:
            query_lower = request.query.lower()
            known_locs = {
                "bengaluru": "Bengaluru, Karnataka", "bangalore": "Bengaluru, Karnataka",
                "maharashtra": "Maharashtra", "mumbai": "Mumbai, Maharashtra",
                "pune": "Pune, Maharashtra", "nagpur": "Nagpur, Maharashtra",
                "ludhiana": "Ludhiana, Punjab", "amritsar": "Amritsar, Punjab",
                "jalandhar": "Jalandhar, Punjab", "punjab": "Punjab",
                "haryana": "Haryana", "karnataka": "Karnataka",
                "kolar": "Kolar, Karnataka", "delhi": "Delhi", "patna": "Patna, Bihar",
                "hyderabad": "Hyderabad, Telangana", "telangana": "Telangana"
            }
            for k, val in known_locs.items():
                if k in query_lower:
                    location = val
                    break

        location = location or "India"
        weather_data = await self.weather_service.get_weather_forecast(location, context)

        # Extract weather parameters dynamically from returned service string if available
        import re
        temp = 30.0
        humidity = 75.0
        rainfall = 0.0

        temp_match = re.search(r"(\d+(?:\.\d+)?)\s*°?C", weather_data, re.IGNORECASE)
        if temp_match:
            temp = float(temp_match.group(1))

        hum_match = re.search(r"(\d+(?:\.\d+)?)\s*%", weather_data)
        if hum_match:
            humidity = float(hum_match.group(1))

        rain_match = re.search(r"(\d+(?:\.\d+)?)\s*mm", weather_data, re.IGNORECASE)
        if rain_match:
            rainfall = float(rain_match.group(1))
        elif "rain" in weather_data.lower():
            rainfall = 25.0

        # Formulate structured WeatherEvidence
        evidence = WeatherEvidence(
            id=f"ev-weather-{context.request_id}",
            source="WeatherService",
            agent=self.name,
            confidence=0.9,
            weight=1.0,
            reasoning=f"Weather forecast for {location}: {weather_data}",
            temperature=temp,
            rainfall=rainfall,
            humidity=humidity,
            ontology_references=["weather_forecast", location.lower()]
        )

        content = f"Weather forecast for {location}: {weather_data}"

        self.state.status = "succeeded"
        self.state.end_time = time.time()
        self.state.execution_time = (self.state.end_time - self.state.start_time) * 1000.0

        return AgentResult(
            agent_name=self.name,
            content=content,
            confidence=0.9,
            metrics={"latency_ms": self.state.execution_time},
            logs=[f"Fetched weather forecast for {location}."],
            evidence=[evidence.model_dump()]
        )


    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        return len(response.content) > 0

    async def cleanup(self) -> None:
        self.state.status = "cleanup"

    async def health_check(self) -> bool:
        return True
