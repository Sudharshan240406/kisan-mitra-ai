import asyncio
import logging
import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.workflows.queue")

class Job(BaseModel):
    """
    Pydantic schema representing a background execution job.
    """
    id: str
    job_type: str  # ai_job, notification, knowledge_refresh, etc.
    payload: Dict[str, Any]
    priority: int = 2  # 1 = High, 2 = Medium, 3 = Low
    status: str = "pending"  # pending, running, completed, failed, retrying
    created_at: float = Field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    attempts: int = 0
    error: Optional[str] = None

class QueueManager:
    """
    Manages in-memory FIFO and priority job queues, storing job details for status lookups.
    """
    def __init__(self, obs_mgr: Any = None) -> None:
        self.obs_mgr = obs_mgr
        self.jobs: Dict[str, Job] = {}
        self.queue: asyncio.Queue[str] = asyncio.Queue()  # Queue stores Job IDs

    async def enqueue(self, job_type: str, payload: Dict[str, Any], priority: int = 2) -> str:
        """
        Enqueues a new background processing job.
        """
        import uuid
        job_id = str(uuid.uuid4())

        from app.tenancy.tenant_context import get_current_tenant_id, get_current_organization_id, get_current_execution_id
        payload.setdefault("tenant_id", get_current_tenant_id())
        payload.setdefault("organization_id", get_current_organization_id())
        payload.setdefault("execution_id", get_current_execution_id() or job_id)

        job = Job(id=job_id, job_type=job_type, payload=payload, priority=priority)
        self.jobs[job_id] = job
        await self.queue.put(job_id)

        if self.obs_mgr:
            self.obs_mgr.metrics_engine.record("queue_depth", self.get_queue_depth(), {"job_type": job_type})

        logger.info(f"[QueueManager] Enqueued job '{job_id}' of type '{job_type}' with priority {priority}")
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """
        Retrieves a job by its ID.
        """
        return self.jobs.get(job_id)

    def get_queue_depth(self) -> int:
        """
        Calculates the number of pending or currently running background jobs.
        """
        return sum(1 for j in self.jobs.values() if j.status in ("pending", "running", "retrying"))
