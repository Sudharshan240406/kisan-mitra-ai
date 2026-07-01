from abc import ABC, abstractmethod
from typing import Any

from app.core.context import AgentContext


class BaseTool(ABC):
    """
    Abstract base class representing an external utility or integration client.
    Can be used by agents to run calculations or hit third-party gateways.
    """
    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @abstractmethod
    async def run(self, args: dict[str, Any], context: AgentContext) -> str:
        """
        Execute tool computation or API fetch.
        """
        pass

    async def health(self) -> dict[str, Any]:
        """
        Default health reporting format for tools.
        """
        return {
            "tool_name": self.name,
            "description": self.description,
            "status": "healthy"
        }
