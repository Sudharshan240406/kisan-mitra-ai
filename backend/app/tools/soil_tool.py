from typing import Any

from app.core.context import AgentContext
from app.core.tool import BaseTool


class SoilTool(BaseTool):
    """
    SoilTool coordinates soil parameter checks.
    """
    def __init__(self) -> None:
        super().__init__(
            name="SoilTool",
            description="Interface client to check soil properties and composition."
        )

    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        return f"SoilTool output for args {args}: Soil pH is 6.5, Nitrogen level is 1.4%."
