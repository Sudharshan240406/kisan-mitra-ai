from app.core.context import AgentContext
from app.tools.soil_tool import SoilTool


class SoilService:
    """
    Domain service encapsulating soil analysis measurements.
    """
    def __init__(self) -> None:
        self.soil_tool = SoilTool()

    async def get_soil_composition(self, location: str, context: AgentContext) -> str:
        """
        Coordinates querying soil properties.
        """
        return await self.soil_tool.run({"location": location}, context)
