import asyncio
import logging
from typing import Any, Awaitable, List, Optional

logger = logging.getLogger("kisan_mitra_ai.performance.concurrency")

class ConcurrencyManager:
    """
    Limits concurrent task workloads during high volume batch operations.
    """
    def __init__(self, default_limit: int = 10) -> None:
        self.default_limit = default_limit

    async def execute_parallel(self, tasks: List[Awaitable[Any]], limit: Optional[int] = None) -> List[Any]:
        """
        Runs list of awaitable coroutines in parallel under a concurrency Semaphore.
        """
        concurrency_limit = limit if limit is not None else self.default_limit
        semaphore = asyncio.Semaphore(concurrency_limit)

        async def _wrapped_task(task: Awaitable[Any]) -> Any:
            async with semaphore:
                return await task

        wrapped_tasks = [_wrapped_task(t) for t in tasks]
        logger.info(f"[ConcurrencyManager] Scheduling {len(tasks)} tasks concurrently (limit: {concurrency_limit})")
        return await asyncio.gather(*wrapped_tasks, return_exceptions=True)


