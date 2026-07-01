import logging
import time
from typing import Any, Optional

from app.core.context import AgentContext
from app.core.knowledge import KnowledgeProvider
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.knowledge.core")


class KnowledgeMetadata(BaseModel):
    """
    Metadata information for knowledge pieces, schemes, or manual records.
    """
    id: str = Field(..., description="Unique document or record ID.")
    source: str = Field(..., description="Authoritative source name (e.g. Gov Portal, AgriManual v1).")
    version: str = Field(default="1.0.0", description="Version identifier.")
    authoritative: bool = Field(default=True, description="Whether the information is official / policy vetted.")
    last_updated: float = Field(default_factory=time.time, description="Epoch timestamp of last data validation.")
    tags: list[str] = Field(default_factory=list, description="Descriptive search labels.")
    extra: dict[str, Any] = Field(default_factory=dict, description="Custom domain properties.")


class KnowledgeCacheEntry(BaseModel):
    """
    Wrapper for cache entries.
    """
    value: Any
    expires_at: float


class KnowledgeCache:
    """
    In-memory caching system with expiration times for agricultural queries.
    """
    def __init__(self, default_ttl: float = 300.0) -> None:
        self.default_ttl = default_ttl
        self._cache: dict[str, KnowledgeCacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        now = time.time()
        entry = self._cache.get(key)
        if entry:
            if entry.expires_at > now:
                self._hits += 1
                return entry.value
            else:
                del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl
        self._cache[key] = KnowledgeCacheEntry(
            value=value,
            expires_at=time.time() + ttl
        )

    def invalidate(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        ratio = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(ratio, 4)
        }


class KnowledgeRegistry:
    """
    Registry for managing swappable Knowledge Providers.
    """
    def __init__(self) -> None:
        self._providers: dict[str, KnowledgeProvider] = {}

    def register(self, key: str, provider: KnowledgeProvider) -> None:
        if key in self._providers:
            logger.warning(f"Knowledge Provider '{key}' is already registered. Overwriting.")
        self._providers[key] = provider
        logger.info(f"Registered Knowledge Provider: {key}")

    def deregister(self, key: str) -> None:
        if key in self._providers:
            del self._providers[key]
            logger.info(f"Deregistered Knowledge Provider: {key}")

    def get(self, key: str) -> KnowledgeProvider:
        if key not in self._providers:
            raise KeyError(f"Knowledge Provider '{key}' is not registered.")
        return self._providers[key]

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())


class KnowledgeVersionManager:
    """
    Manages document version tracking, auditing updates, and ensuring fresh records.
    """
    def __init__(self) -> None:
        self._versions: dict[str, list[KnowledgeMetadata]] = {}

    def register_version(self, meta: KnowledgeMetadata) -> None:
        if meta.id not in self._versions:
            self._versions[meta.id] = []
        self._versions[meta.id].append(meta)
        # Sort versions in reverse chronological order
        self._versions[meta.id].sort(key=lambda x: x.last_updated, reverse=True)
        logger.debug(f"Registered document version {meta.version} for document {meta.id}")

    def get_latest(self, doc_id: str) -> Optional[KnowledgeMetadata]:
        history = self._versions.get(doc_id)
        if history:
            return history[0]
        return None

    def get_history(self, doc_id: str) -> list[KnowledgeMetadata]:
        return self._versions.get(doc_id, [])


class KnowledgeManager:
    """
    Orchestrates search dispatches, updates metadata catalogs, and coordinates cache validation.
    """
    def __init__(self) -> None:
        self.registry = KnowledgeRegistry()
        self.cache = KnowledgeCache()
        self.version_manager = KnowledgeVersionManager()

    async def query_provider(
        self,
        provider_key: str,
        query: str,
        limit: int = 5,
        context: Optional[AgentContext] = None
    ) -> list[dict[str, Any]]:
        """
        Queries a specific provider using caching layer to avoid redundant evaluations.
        """
        cache_key = f"{provider_key}:{query}:{limit}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        provider = self.registry.get(provider_key)
        results = await provider.search(query, limit=limit, context=context)
        self.cache.set(cache_key, results)
        return results


class KnowledgePlatform:
    """
    Unified entry point representing the complete Kisan Mitra Knowledge Platform.
    """
    def __init__(self) -> None:
        self.manager = KnowledgeManager()
        self.graph: Optional[Any] = None
        logger.info("Kisan Mitra Agricultural Knowledge Platform successfully bootstrapped.")

    def health(self) -> dict[str, Any]:
        """
        Gathers statuses across all registered subsystems.
        """
        providers_status = {}
        for p_key in self.manager.registry.list_providers():
            try:
                providers_status[p_key] = self.manager.registry.get(p_key).health()
            except Exception as e:
                providers_status[p_key] = {"status": "unhealthy", "error": str(e)}

        return {
            "status": "healthy",
            "registered_providers": self.manager.registry.list_providers(),
            "providers_health": providers_status,
            "cache_stats": self.manager.cache.stats
        }
