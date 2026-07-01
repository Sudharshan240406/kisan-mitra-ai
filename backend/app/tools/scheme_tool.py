from typing import Any

from app.core.context import AgentContext
from app.core.tool import BaseTool


class GovernmentSchemeTool(BaseTool):
    """
    GovernmentSchemeTool scans agricultural welfare program schemas.
    """
    def __init__(self) -> None:
        super().__init__(
            name="GovernmentSchemeTool",
            description="Interface client to query official subsidy program parameters."
        )

    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        return "GovernmentSchemeTool output: Found PM-KISAN subsidy details."
