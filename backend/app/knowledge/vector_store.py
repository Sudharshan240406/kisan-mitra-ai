import logging
from abc import abstractmethod
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.knowledge import KnowledgeProvider

logger = logging.getLogger("kisan_mitra_ai.knowledge.vector_store")


class VectorStore(KnowledgeProvider):
    """
    Abstract interface defining vector database index actions.
    All swappable vector engines must implement this class.
    """
    @abstractmethod
    async def similarity_search(
        self,
        query: str,
        limit: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """
        Calculates similarity distances between query vector embeddings and doc index.
        """
        pass

    async def search(
        self,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        """
        KnowledgeProvider search adapter routing directly to similarity search.
        """
        filter_dict = None
        if context and context.crop:
            filter_dict = {"crop": context.crop}
        return await self.similarity_search(query, limit=limit, metadata_filter=filter_dict)

    @abstractmethod
    def get_document_count(self) -> int:
        """
        Returns number of indexed records.
        """
        pass


class FAISSVectorStore(VectorStore):
    """
    Mock implementation of a local FAISS index.
    """
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    async def similarity_search(
        self,
        query: str,
        limit: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"FAISS: Performing similarity search for query '{query}'")
        matches = []
        for doc in self.documents:
            # Simple keyword overlap mock similarity score
            query_words = set(query.lower().split())
            doc_words = set(doc["content"].lower().split())
            overlap = len(query_words.intersection(doc_words))
            score = overlap / len(query_words) if query_words else 0.0

            if metadata_filter:
                match_filter = all(doc["metadata"].get(k) == v for k, v in metadata_filter.items())
                if not match_filter:
                    continue

            matches.append({
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": round(score, 4),
                "source": "faiss"
            })
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        self.documents.append({"content": content, "metadata": metadata})
        logger.debug(f"FAISS: Indexed new document. Total size: {len(self.documents)}")

    def get_document_count(self) -> int:
        return len(self.documents)

    def health(self) -> dict[str, Any]:
        return {
            "provider": "FAISS",
            "status": "healthy",
            "document_count": len(self.documents),
            "type": "in-memory-mock"
        }


class ChromaVectorStore(VectorStore):
    """
    Mock/adapter implementation for ChromaDB vector registry.
    """
    def __init__(self, db_path: str = "./data/vector_db") -> None:
        self.db_path = db_path
        self.documents: list[dict[str, Any]] = []

    async def similarity_search(
        self,
        query: str,
        limit: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Chroma: Performing similarity search for query '{query}'")
        matches = []
        for doc in self.documents:
            # Simple simulation
            score = 0.85 if any(word in doc["content"].lower() for word in query.lower().split()) else 0.1
            if metadata_filter:
                match_filter = all(doc["metadata"].get(k) == v for k, v in metadata_filter.items())
                if not match_filter:
                    continue
            matches.append({
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": score,
                "source": "chroma"
            })
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        self.documents.append({"content": content, "metadata": metadata})

    def get_document_count(self) -> int:
        return len(self.documents)

    def health(self) -> dict[str, Any]:
        return {
            "provider": "ChromaDB",
            "status": "healthy",
            "db_path": self.db_path,
            "document_count": len(self.documents),
            "type": "mock"
        }


class QdrantVectorStore(VectorStore):
    """
    Mock implementation of Qdrant vector database.
    """
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    async def similarity_search(
        self,
        query: str,
        limit: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Qdrant: Similarity search for query '{query}'")
        matches = []
        for doc in self.documents:
            score = 0.80 if any(word in doc["content"].lower() for word in query.lower().split()) else 0.15
            if metadata_filter:
                match_filter = all(doc["metadata"].get(k) == v for k, v in metadata_filter.items())
                if not match_filter:
                    continue
            matches.append({
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": score,
                "source": "qdrant"
            })
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        self.documents.append({"content": content, "metadata": metadata})

    def get_document_count(self) -> int:
        return len(self.documents)

    def health(self) -> dict[str, Any]:
        return {
            "provider": "Qdrant",
            "status": "healthy",
            "document_count": len(self.documents),
            "type": "mock"
        }


class PineconeVectorStore(VectorStore):
    """
    Mock implementation of Pinecone cloud vector database.
    """
    def __init__(self) -> None:
        self.documents: list[dict[str, Any]] = []

    async def similarity_search(
        self,
        query: str,
        limit: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        logger.info(f"Pinecone: Similarity search for query '{query}'")
        matches = []
        for doc in self.documents:
            score = 0.78 if any(word in doc["content"].lower() for word in query.lower().split()) else 0.20
            if metadata_filter:
                match_filter = all(doc["metadata"].get(k) == v for k, v in metadata_filter.items())
                if not match_filter:
                    continue
            matches.append({
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": score,
                "source": "pinecone"
            })
        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches[:limit]

    async def index_document(self, content: str, metadata: dict[str, Any]) -> None:
        self.documents.append({"content": content, "metadata": metadata})

    def get_document_count(self) -> int:
        return len(self.documents)

    def health(self) -> dict[str, Any]:
        return {
            "provider": "Pinecone",
            "status": "healthy",
            "document_count": len(self.documents),
            "type": "mock"
        }
