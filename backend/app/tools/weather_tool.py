from typing import Any

from app.core.context import AgentContext
from app.core.tool import BaseTool


class WeatherTool(BaseTool):
    """
    WeatherTool coordinates meteorological queries with weather services.
    """
    def __init__(self) -> None:
        super().__init__(
            name="WeatherTool",
            description="Interface parameter client for weather forecasts and local indices."
        )

    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        return f"WeatherTool output for args {args}: Forecast is 30C with low rainfall probability."
