import asyncio
import datetime
import logging
import time
import uuid
from typing import Any, Callable, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("kisan_mitra_ai.workflows.scheduler")

class ScheduledJob(BaseModel):
    """
    Schema describing a scheduled event or cron job.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    job_type: str  # cron, interval, one_time, event_driven
    schedule: str  # Cron expression, interval seconds, or event name
    callback: Callable[..., Any] = Field(..., exclude=True)  # Exclude from dictionary conversions
    last_run: float = 0.0
    next_run: float = 0.0
    active: bool = True

    model_config = ConfigDict(arbitrary_types_allowed=True)

class Scheduler:
    """
    Cron and interval scheduler using background scheduling loops.
    """
    def __init__(self, workflow_mgr: Any = None) -> None:
        self.workflow_mgr = workflow_mgr
        self.jobs: Dict[str, ScheduledJob] = {}
        self._loop_task: Optional[asyncio.Task[Any]] = None
        self._running = False

    def start(self) -> None:
        """
        Starts the background scheduler loop.
        """
        self._running = True
        self._loop_task = asyncio.create_task(self._scheduler_loop())
        logger.info("[Scheduler] Started background scheduling loop")

    async def stop(self) -> None:
        """
        Stops the background scheduler loop.
        """
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
            self._loop_task = None
        logger.info("[Scheduler] Stopped background scheduling loop")

    def schedule_cron(self, name: str, cron_expr: str, callback: Callable[..., Any]) -> str:
        """
        Registers a job matching standard cron patterns.
        """
        job = ScheduledJob(
            name=name,
            job_type="cron",
            schedule=cron_expr,
            callback=callback,
            next_run=self._calculate_next_cron(cron_expr, time.time())
        )
        self.jobs[job.id] = job
        logger.info(f"[Scheduler] Scheduled cron job '{name}' with pattern '{cron_expr}'")
        return job.id

    def schedule_interval(self, name: str, seconds: float, callback: Callable[..., Any]) -> str:
        """
        Registers a job running every N seconds.
        """
        job = ScheduledJob(
            name=name,
            job_type="interval",
            schedule=str(seconds),
            callback=callback,
            next_run=time.time() + seconds
        )
        self.jobs[job.id] = job
        logger.info(f"[Scheduler] Scheduled interval job '{name}' every {seconds}s")
        return job.id

    def schedule_one_time(self, name: str, delay_seconds: float, callback: Callable[..., Any]) -> str:
        """
        Registers a job executing once after N seconds.
        """
        job = ScheduledJob(
            name=name,
            job_type="one_time",
            schedule=str(delay_seconds),
            callback=callback,
            next_run=time.time() + delay_seconds
        )
        self.jobs[job.id] = job
        logger.info(f"[Scheduler] Scheduled one-time job '{name}' in {delay_seconds}s")
        return job.id

    def schedule_event(self, name: str, event_name: str, callback: Callable[..., Any]) -> str:
        """
        Registers a job waiting for a platform event trigger.
        """
        job = ScheduledJob(
            name=name,
            job_type="event_driven",
            schedule=event_name,
            callback=callback
        )
        self.jobs[job.id] = job
        logger.info(f"[Scheduler] Scheduled event-driven job '{name}' trigger '{event_name}'")
        return job.id

    def trigger_event(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        """
        Triggers execution of all event-driven jobs registered under this event.
        """
        for job in self.jobs.values():
            if job.job_type == "event_driven" and job.schedule == event_name and job.active:
                logger.info(f"[Scheduler] Triggering event job '{job.name}' on event '{event_name}'")
                asyncio.create_task(self._run_job_callback(job, *args, **kwargs))

    async def _scheduler_loop(self) -> None:
        while self._running:
            try:
                now = time.time()
                for job in list(self.jobs.values()):
                    if not job.active:
                        continue

                    # Check if due
                    if job.job_type in ("cron", "interval", "one_time") and now >= job.next_run:
                        logger.info(f"[Scheduler] Scheduled job '{job.name}' is due, executing...")
                        asyncio.create_task(self._run_job_callback(job))

                        job.last_run = now
                        if job.job_type == "interval":
                            job.next_run = now + float(job.schedule)
                        elif job.job_type == "cron":
                            job.next_run = self._calculate_next_cron(job.schedule, now)
                        elif job.job_type == "one_time":
                            job.active = False

                await asyncio.sleep(1.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Scheduler] Loop exception: {e}")
                await asyncio.sleep(5.0)

    async def _run_job_callback(self, job: ScheduledJob, *args: Any, **kwargs: Any) -> None:
        try:
            if asyncio.iscoroutinefunction(job.callback):
                await job.callback(*args, **kwargs)
            else:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, lambda: job.callback(*args, **kwargs))
        except Exception as e:
            logger.error(f"[Scheduler] Job '{job.name}' callback failure: {e}")

    def _calculate_next_cron(self, cron_expr: str, base_time: float) -> float:
        parts = cron_expr.split()
        if len(parts) != 5:
            return base_time + 60.0

        dt = datetime.datetime.fromtimestamp(base_time)
        dt = dt.replace(second=0, microsecond=0)

        # Max search: 7 days
        for _ in range(10080):
            dt += datetime.timedelta(minutes=1)

            if not self._match_field(parts[0], dt.minute):
                continue
            if not self._match_field(parts[1], dt.hour):
                continue
            if not self._match_field(parts[2], dt.day):
                continue
            if not self._match_field(parts[3], dt.month):
                continue

            # Match weekday standard: 0 or 7 is Sunday, 1 is Monday... 6 is Saturday
            cron_day = dt.weekday() + 1
            if cron_day == 7:
                cron_day = 0
            if not self._match_field(parts[4], cron_day):
                continue

            return dt.timestamp()

        return base_time + 60.0

    def _match_field(self, field: str, val: int) -> bool:
        if field == "*":
            return True
        if "/" in field:
            base, step = field.split("/")
            step_val = int(step)
            if base == "*":
                return val % step_val == 0
            return (val - int(base)) % step_val == 0
        if "," in field:
            return str(val) in field.split(",")
        if "-" in field:
            start, end = field.split("-")
            return int(start) <= val <= int(end)
        return int(field) == val
