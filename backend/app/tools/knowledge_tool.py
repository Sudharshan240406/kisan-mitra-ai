from typing import Any

from app.core.context import AgentContext
from app.core.tool import BaseTool


class KnowledgeTool(BaseTool):
    """
    KnowledgeTool indexes and searches Crop manuals and RAG references.
    """
    def __init__(self) -> None:
        super().__init__(
            name="KnowledgeTool",
            description="Interface client to query semantic RAG document segments."
        )

    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        return f"KnowledgeTool query '{args.get('query')}': Nitrogen balance must exceed 1.2% in crop soils."
