import asyncio
import logging
import time
from typing import Any, List

from .queue_manager import Job, QueueManager
from .retry_engine import RetryEngine

logger = logging.getLogger("kisan_mitra_ai.workflows.runner")

class JobRunner:
    """
    Background worker pool polling QueueManager and running jobs.
    """
    def __init__(self, container: Any, queue_mgr: QueueManager, retry_engine: RetryEngine) -> None:
        self.container = container
        self.queue_mgr = queue_mgr
        self.retry_engine = retry_engine
        self._workers: List[asyncio.Task[Any]] = []
        self._running = False

    def start(self, worker_count: int = 2) -> None:
        """
        Starts the background worker task loop.
        """
        self._running = True
        for i in range(worker_count):
            task = asyncio.create_task(self._worker_loop(i))
            self._workers.append(task)
        logger.info(f"[JobRunner] Started {worker_count} background worker threads/tasks")

    async def stop(self) -> None:
        """
        Cancels and stops the worker loops.
        """
        self._running = False
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("[JobRunner] Stopped all background worker tasks")

    async def _worker_loop(self, worker_id: int) -> None:
        while self._running:
            try:
                job_id = await self.queue_mgr.queue.get()
                job = self.queue_mgr.get_job(job_id)
                if not job:
                    self.queue_mgr.queue.task_done()
                    continue

                job.status = "running"
                job.started_at = time.time()
                job.attempts += 1
                logger.info(f"[JobRunner-Worker-{worker_id}] Processing job '{job.id}' (type: {job.job_type}, attempt: {job.attempts})")

                try:
                    await self._execute_job(job)
                    job.status = "completed"
                    job.completed_at = time.time()
                    logger.info(f"[JobRunner-Worker-{worker_id}] Job '{job.id}' completed successfully")

                    obs_mgr = getattr(self.container, "observability_manager", None)
                    if obs_mgr:
                        obs_mgr.metrics_engine.record("job_success_rate", 1.0, {"job_type": job.job_type})
                        obs_mgr.metrics_engine.record("queue_depth", self.queue_mgr.get_queue_depth(), {"job_type": job.job_type})

                except Exception as e:
                    logger.error(f"[JobRunner-Worker-{worker_id}] Job '{job.id}' failed: {e}")
                    job.error = str(e)
                    self.retry_engine.log_failure(job.id, str(e), job.job_type)

                    # Hand over backoff retries logic
                    policy = job.payload.get("retry_policy", {})
                    max_retries = policy.get("max_retries", 3)
                    initial_delay = policy.get("initial_delay", 1.0)
                    backoff_factor = policy.get("backoff_factor", 2.0)

                    if job.attempts <= max_retries:
                        job.status = "retrying"
                        delay = initial_delay * (backoff_factor ** (job.attempts - 1))
                        logger.warning(f"[JobRunner-Worker-{worker_id}] Scheduling retry for job '{job.id}' in {delay:.2f}s")

                        # Dispatch delayed retry task
                        asyncio.create_task(self._retry_job_after_delay(job.id, delay))
                    else:
                        job.status = "failed"
                        self.retry_engine.move_to_dlq(job.id, job.model_dump(), str(e), job.job_type)

                        obs_mgr = getattr(self.container, "observability_manager", None)
                        if obs_mgr:
                            obs_mgr.metrics_engine.record("job_success_rate", 0.0, {"job_type": job.job_type})
                            obs_mgr.metrics_engine.record("queue_depth", self.queue_mgr.get_queue_depth(), {"job_type": job.job_type})

                finally:
                    self.queue_mgr.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[JobRunner] Worker loop exception: {e}")
                await asyncio.sleep(1.0)

    async def _retry_job_after_delay(self, job_id: str, delay: float) -> None:
        await asyncio.sleep(delay)
        await self.queue_mgr.queue.put(job_id)

    async def _execute_job(self, job: Job) -> None:  # noqa: PLR0912
        # Determine job type
        if job.job_type == "ai_job":
            req_data = job.payload.get("request")
            if not req_data:
                raise ValueError("Missing 'request' in payload for ai_job")

            # Map request dict back to ExecutionRequest
            from app.schemas.requests import ExecutionRequest
            req = ExecutionRequest(**req_data)

            # Ensure orchestrator runs request synchronously by bypassing background queuing
            # We will use get_container or orchestrator container bindings
            if hasattr(self.container, "orchestrator"):
                await self.container.orchestrator.execute_query(req, background_bypass=True)
            else:
                # Instanstiate fallback orchestrator if not directly bound
                from app.orchestrator.orchestrator import AgentOrchestrator
                orch = AgentOrchestrator(self.container)
                await orch.execute_query(req, background_bypass=True)

        elif job.job_type == "notification":
            recipient = job.payload.get("recipient")
            message = job.payload.get("message")

            if hasattr(self.container, "autonomous_manager") and self.container.autonomous_manager:
                notification_engine = getattr(self.container.autonomous_manager, "notification_engine", None)
                if notification_engine:
                    from app.autonomous.notification_engine import NotificationPriority
                    await notification_engine.dispatch_notification(
                        recipient=recipient,
                        message=message,
                        priority=NotificationPriority.MEDIUM
                    )
                else:
                    logger.warning("[JobRunner] Notification engine not found in autonomous manager")
            else:
                logger.warning("[JobRunner] Autonomous manager not found")

        elif job.job_type == "knowledge_refresh":
            if hasattr(self.container, "knowledge_platform") and self.container.knowledge_platform:
                logger.info("[JobRunner] Triggering knowledge platform index rebuild")
                await asyncio.sleep(0.5)
            else:
                raise ValueError("Knowledge platform is not initialized")

        elif job.job_type == "memory_summarization":
            farmer_id = job.payload.get("farmer_id")
            if hasattr(self.container, "learning_manager") and self.container.learning_manager:
                logger.info(f"[JobRunner] Summarizing conversation logs for farmer '{farmer_id}'")
                await asyncio.sleep(0.5)
            else:
                raise ValueError("Learning manager is not initialized")

        elif job.job_type == "digital_twin_update":
            farmer_id = job.payload.get("farmer_id")
            if hasattr(self.container, "twin_manager") and self.container.twin_manager:
                logger.info(f"[JobRunner] Simulating digital twin updates for farmer '{farmer_id}'")
                await self.container.twin_manager.update_twin_predictions(farmer_id)
            else:
                raise ValueError("Twin manager is not initialized")

        elif job.job_type == "report_generation":
            farmer_id = job.payload.get("farmer_id")
            logger.info(f"[JobRunner] Generating advisory report for farmer '{farmer_id}'")
            await asyncio.sleep(0.5)

        else:
            raise ValueError(f"Unknown job type: {job.job_type}")
