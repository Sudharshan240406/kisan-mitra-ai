from app.core.context import AgentContext
from app.tools.weather_tool import WeatherTool


class WeatherService:
    """
    Domain service encapsulating weather analytics and tool execution coordinating.
    """
    def __init__(self) -> None:
        self.weather_tool = WeatherTool()

    async def get_weather_forecast(self, location: str, context: AgentContext) -> str:
        """
        Coordinates fetching weather forecasts, using active integration if configured.
        """
        container = context.metadata.get("container") if context else None
        if container and hasattr(container, "integration_registry"):
            active_adapter = container.integration_registry.get_active("weather")
            if active_adapter:
                # Execute resilient weather forecast fetch
                try:
                    result = await container.resilient_runner.execute(
                        integration_id=active_adapter.metadata.id,
                        operation_name="get_forecast",
                        func=lambda: active_adapter.get_forecast(location),
                        trace_id=context.trace_id,
                        request_id=context.request_id,
                        session_id=context.session_id
                    )
                    warnings_str = ", ".join(result.get("warnings", []))
                    return (
                        f"Weather Integration ({active_adapter.metadata.name}) output: "
                        f"Forecast for {location} is {result.get('temperature_c')}C with "
                        f"{result.get('humidity_pct')}% humidity. Warnings: {warnings_str or 'None'}."
                    )
                except Exception as e:
                    return f"Weather Integration ({active_adapter.metadata.name}) failed: {e!s}. Falling back to default forecast."

        return await self.weather_tool.run({"location": location}, context)
