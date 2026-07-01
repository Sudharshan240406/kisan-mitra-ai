from app.core.context import AgentContext
from app.tools.market_tool import MarketTool


class MarketService:
    """
    Domain service encapsulating Mandi prices data and tool execution coordinating.
    """
    def __init__(self) -> None:
        self.market_tool = MarketTool()

    async def get_market_prices(self, commodity: str, location: str, context: AgentContext) -> str:
        """
        Coordinates fetching mandi commodity prices, using active integration if configured.
        """
        container = context.metadata.get("container") if context else None
        if container and hasattr(container, "integration_registry"):
            active_adapter = container.integration_registry.get_active("market")
            if active_adapter:
                try:
                    result = await container.resilient_runner.execute(
                        integration_id=active_adapter.metadata.id,
                        operation_name="get_market_price",
                        func=lambda: active_adapter.get_market_price(commodity, location),
                        trace_id=context.trace_id,
                        request_id=context.request_id,
                        session_id=context.session_id
                    )
                    return (
                        f"Market Integration ({active_adapter.metadata.name}) output: "
                        f"Mandi rates for {commodity} in {location} - "
                        f"Modal Price: Rs {result.get('modal_price_per_quintal')}/quintal "
                        f"(Range: Rs {result.get('min_price_per_quintal')} - {result.get('max_price_per_quintal')})."
                    )
                except Exception as e:
                    return f"Market Integration ({active_adapter.metadata.name}) failed: {e!s}. Falling back to default rates."

        return await self.market_tool.run({"commodity": commodity, "location": location}, context)
