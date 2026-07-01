from app.core.context import AgentContext
from app.intelligence.arm import AgriculturalReasoningMemory
from app.tools.memory_tool import MemoryTool


class MemoryService:
    """
    Domain service encapsulating agricultural memory and history logs.
    """
    def __init__(self, arm: AgriculturalReasoningMemory) -> None:
        self.memory_tool = MemoryTool()
        self.arm = arm

    async def get_farmer_history(self, farmer_id: str, context: AgentContext) -> str:
        """
        Coordinates loading farmer history profiles.
        """
        return await self.memory_tool.run({"farmer_id": farmer_id}, context)
