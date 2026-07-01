from abc import ABC, abstractmethod
from typing import Any

from app.core.context import AgentContext


class KnowledgeProvider(ABC):
    """
    Abstract interface for managing Retrieval-Augmented Generation (RAG)
    knowledge bases, document vector registries, and manual lookups.
    """
    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 5,
        context: AgentContext | None = None
    ) -> list[dict[str, Any]]:
        """
        Query the indexed database for evolution parameters or agricultural recommendations.
        """
        pass

    @abstractmethod
    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        """
        Store a new policy, Crop manual, or agricultural advisory text.
        """
        pass

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """
        Exposes connection status and document counts.
        """
        pass


class ChromaDBKnowledgeProvider(KnowledgeProvider):
    """
    Concrete interface client pointing to persistent vector registers (ChromaDB).
    """
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port

    async def search(self, query: str, limit: int = 5, context: AgentContext | None = None) -> list[dict[str, Any]]:
        return [{"source": "chroma", "content": f"Mock search match for '{query}'"}]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {"provider": "ChromaDB", "status": "healthy", "host": self.host}


class GovDocsKnowledgeProvider(KnowledgeProvider):
    """
    Concrete interface client pointing to official policy registers.
    """
    async def search(self, query: str, limit: int = 5, context: AgentContext | None = None) -> list[dict[str, Any]]:
        return [{"source": "gov_docs", "content": f"Official document match for '{query}'"}]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {"provider": "GovDocs", "status": "healthy"}


class ManualsKnowledgeProvider(KnowledgeProvider):
    """
    Concrete interface client pointing to agronomic cultivation manuals.
    """
    async def search(self, query: str, limit: int = 5, context: AgentContext | None = None) -> list[dict[str, Any]]:
        return [{"source": "manuals", "content": f"Agronomic manual details for '{query}'"}]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {"provider": "Manuals", "status": "healthy"}


class ResearchPapersKnowledgeProvider(KnowledgeProvider):
    """
    Concrete interface client pointing to academic journals.
    """
    async def search(self, query: str, limit: int = 5, context: AgentContext | None = None) -> list[dict[str, Any]]:
        return [{"source": "research", "content": f"Scientific research findings for '{query}'"}]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {"provider": "ResearchPapers", "status": "healthy"}


class MarketBulletinsKnowledgeProvider(KnowledgeProvider):
    """
    Concrete interface client pointing to economic market bulletins.
    """
    async def search(self, query: str, limit: int = 5, context: AgentContext | None = None) -> list[dict[str, Any]]:
        return [{"source": "market_bulletins", "content": f"Commodity trend indexes for '{query}'"}]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {"provider": "MarketBulletins", "status": "healthy"}


class WeatherKnowledgeProvider(KnowledgeProvider):
    """
    Concrete interface client pointing to meteorological data.
    """
    async def search(self, query: str, limit: int = 5, context: AgentContext | None = None) -> list[dict[str, Any]]:
        return [{"source": "weather_data", "content": f"Climatic patterns record for '{query}'"}]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        pass

    def health(self) -> dict[str, Any]:
        return {"provider": "WeatherKnowledge", "status": "healthy"}
