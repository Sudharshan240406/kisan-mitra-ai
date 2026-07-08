import logging
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel

logger = logging.getLogger("kisan_mitra_ai.performance.cache_engine")

class CacheEntry(BaseModel):
    """
    Schema representing a cached item with an expiration window.
    """
    value: Any
    expires_at: float

class CacheEngine:
    """
    In-memory Key-Value cache with TTL-based expiration tracking.
    """
    def __init__(self, default_ttl: float = 300.0) -> None:
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a cached value, checking if it is still fresh.
        """
        entry = self._cache.get(key)
        now = time.time()
        if entry:
            if entry.expires_at > now:
                self._hits += 1
                return entry.value
            else:
                # Evict expired entry
                del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """
        Inserts/updates cache entry with configured TTL window.
        """
        duration = ttl if ttl is not None else self.default_ttl
        expires_at = time.time() + duration
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    def invalidate(self, key: str) -> None:
        """
        Evicts a specific key from cache.
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """
        Clears all cached entries and stats.
        """
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def hit_ratio(self) -> float:
        """
        Returns current hit-to-total ratio.
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(self.hit_ratio, 4)
        }
