from typing import Any

from app.core.context import AgentContext
from app.core.tool import BaseTool


class MarketTool(BaseTool):
    """
    MarketTool coordinates commodity Mandi pricing data pulls.
    """
    def __init__(self) -> None:
        super().__init__(
            name="MarketTool",
            description="Interface client to fetch mandi crop prices."
        )

    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        return f"MarketTool output for args {args}: Price of wheat is 2200 INR per Quintal."
