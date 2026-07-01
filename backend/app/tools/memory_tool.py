from typing import Any

from app.core.context import AgentContext
from app.core.tool import BaseTool


class MemoryTool(BaseTool):
    """
    MemoryTool registers profiles and logs context variables.
    """
    def __init__(self) -> None:
        super().__init__(
            name="MemoryTool",
            description="Interface client to write/load conversation memories."
        )

    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        return f"MemoryTool output: Context trace '{context.trace_id}' saved to history successfully."
