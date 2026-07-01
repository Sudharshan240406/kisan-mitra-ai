import logging
from abc import ABC, abstractmethod
from typing import Any

from app.core.context import AgentContext
from app.core.llm_provider import BaseLLMProvider
from app.core.state import AgentState
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResult


class BaseAgent(ABC):
    """
    Abstract base class for all Kisan Mitra AI specialized agents.
    Defines the standard execution lifecycle, validation check gates,
    state tracking, and automatic structured logging inheritances.
    """
    def __init__(self, name: str, llm_provider: BaseLLMProvider) -> None:
        self.name = name
        self.llm_provider = llm_provider
        self.state = AgentState()
        self.logger = logging.getLogger(f"kisan_mitra_ai.agents.{name}")
        self.logger.info(f"Agent '{self.name}' successfully loaded into memory.")

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the agent resources, load vector databases, cache indexes, etc.
        """
        pass

    @abstractmethod
    async def execute(self, request: AgentRequest, context: AgentContext) -> AgentResult:
        """
        Execute core query reasoning on the LLM or query dynamic parameters.
        Must return standard AgentResult model.
        """
        pass

    @abstractmethod
    async def validate(self, response: AgentResult, context: AgentContext) -> bool:
        """
        Syntactically or semantically validate the agent response prior to egress.
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """
        Cleanup open connections, file streams, or memory registers.
        """
        pass

    async def health(self) -> dict[str, Any]:
        """
        Exposes health metrics and dynamic states for this specific agent.
        """
        provider_ok = False
        try:
            provider_ok = self.llm_provider.get_model_name() is not None
        except Exception:
            pass

        return {
            "agent_name": self.name,
            "status": self.state.status,
            "provider_connected": provider_ok,
            "errors": self.state.errors,
            "warnings": self.state.warnings,
            "metrics": self.state.metrics
        }

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Execute ping checks to check downstream resource statuses specific to this agent.
        """
        pass
