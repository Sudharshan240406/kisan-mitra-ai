from abc import ABC, abstractmethod
from typing import Any


class SessionMemory(ABC):
    """
    Abstract interface for managing active user session history.
    """
    @abstractmethod
    async def get_session_history(self, session_id: str) -> list[dict[str, Any]]:
        """
        Fetch conversation logs associated with a session ID.
        """
        pass

    @abstractmethod
    async def save_session_message(self, session_id: str, role: str, content: str) -> None:
        """
        Save an individual message (user/assistant role) to the session history.
        """
        pass

    @abstractmethod
    async def clear_session(self, session_id: str) -> None:
        """
        Delete session records.
        """
        pass


class ConversationMemory(ABC):
    """
    Abstract interface for executing transient in-memory operations
    spanning individual nested execution runs.
    """
    @abstractmethod
    async def get_context_memory(self, trace_id: str) -> dict[str, Any]:
        """
        Retrieve shared execution memory dict for a transaction run.
        """
        pass

    @abstractmethod
    async def update_context_memory(self, trace_id: str, data: dict[str, Any]) -> None:
        """
        Merge/update variables in the transaction run memory context.
        """
        pass


class FarmerMemory(ABC):
    """
    Abstract interface representing profile caches for registered farmers.
    """
    @abstractmethod
    async def get_farmer_profile(self, farmer_id: str) -> dict[str, Any] | None:
        """
        Load profile details (language preferred, geolocation data, soil logs).
        """
        pass

    @abstractmethod
    async def update_farmer_profile(self, farmer_id: str, profile_data: dict[str, Any]) -> None:
        """
        Save or update profile parameters.
        """
        pass


class LongTermMemory(ABC):
    """
    Abstract interface for semantic profile updates and episodic recall vectors.
    """
    @abstractmethod
    async def recall_relevant_contexts(
        self,
        farmer_id: str,
        query: str,
        limit: int = 3
    ) -> list[dict[str, Any]]:
        """
        Recall facts or advice logs relevant to the farmer's current inquiry.
        """
        pass

    @abstractmethod
    async def commit_to_long_term(self, farmer_id: str, fact: str, metadata: dict[str, Any]) -> None:
        """
        Log an agronomic fact, crop cycle step, or profile parameter permanently.
        """
        pass
