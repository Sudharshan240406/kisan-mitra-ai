import asyncio
import logging
from typing import Any, Callable, Generic, TypeVar

logger = logging.getLogger("kisan_mitra_ai.performance.resource_pool")

T = TypeVar("T")

class ResourceContext(Generic[T]):
    """
    Context manager representing resource lease duration lifecycle.
    """
    def __init__(self, pool: "ResourcePool[T]", resource: T) -> None:
        self.pool = pool
        self.resource = resource

    async def __aenter__(self) -> T:
        return self.resource

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.pool.release(self.resource)

class ResourcePool(Generic[T]):
    """
    Pool container implementing concurrent checkout limits.
    """
    def __init__(self, factory: Callable[[], T], max_size: int = 5) -> None:
        self.factory = factory
        self.max_size = max_size
        self._queue: asyncio.Queue[T] = asyncio.Queue(max_size)
        self._created = 0
        self._lock = asyncio.Lock()

    async def acquire(self) -> ResourceContext[T]:
        """
        Leases a resource from the pool, creating a new instance if capacity allows.
        """
        async with self._lock:
            # If queue is empty and we haven't hit max_size, instantiate resource
            if self._queue.empty() and self._created < self.max_size:
                resource = self.factory()
                self._created += 1
                logger.debug(f"[ResourcePool] Created new resource instance. Total: {self._created}/{self.max_size}")
                return ResourceContext(self, resource)

        # Block until a resource is returned to queue
        resource = await self._queue.get()
        return ResourceContext(self, resource)

    async def release(self, resource: T) -> None:
        """
        Returns resource back to pool queue.
        """
        await self._queue.put(resource)
        self._queue.task_done()
        logger.debug("[ResourcePool] Resource returned to pool.")

    def get_utilization(self) -> float:
        """
        Calculates lease occupancy utilization.
        """
        checked_out = self._created - self._queue.qsize()
        return checked_out / self.max_size if self.max_size > 0 else 0.0
