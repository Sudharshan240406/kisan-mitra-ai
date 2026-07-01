import logging

from agents.base import BaseAgent
from app.core.exceptions import AgentException

logger = logging.getLogger("kisan_mitra_ai")

class AgentRegistry:
    """
    Centralized Registry for registering, retrieving, and discovering
    active Kisan Mitra AI agents, supporting runtime dependency mapping.
    """
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}
        logger.info("Centralized AgentRegistry initialized.")

    def register(self, agent: BaseAgent) -> None:
        """
        Registers an active agent instance. Validates uniqueness of naming tags.
        """
        if not isinstance(agent, BaseAgent):
            raise AgentException("Only instances inheriting from BaseAgent can be registered.")

        name_key = agent.name.strip().lower()
        if not name_key:
            raise AgentException("Registered agent must have a non-empty name attribute.")

        if name_key in self._agents:
            raise AgentException(f"An agent named '{agent.name}' has already been registered.")

        self._agents[name_key] = agent
        logger.info(f"Registered agent '{agent.name}' into AgentRegistry.")

    def get(self, agent_name: str) -> BaseAgent:
        """
        Retrieves the agent by its registered name case-insensitively.
        """
        name_key = agent_name.strip().lower()
        agent = self._agents.get(name_key)
        if not agent:
            raise AgentException(f"Agent '{agent_name}' was not found in the registry.")
        return agent

    def list_agents(self) -> list[str]:
        """
        Returns a list of all currently registered agent names.
        """
        return [agent.name for agent in self._agents.values()]
