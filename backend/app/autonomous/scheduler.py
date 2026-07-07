import logging
import time
from typing import Any, Callable, Dict, List

logger = logging.getLogger("kisan_mitra_ai.autonomous.scheduler")

class Scheduler:
    """
    Coordinates periodic (daily, weekly, monthly) and event-driven action triggers.
    """
    def __init__(self) -> None:
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.execution_log: List[Dict[str, Any]] = []

    def register_job(self, name: str, schedule_type: str, callback: Callable[..., Any]) -> None:
        """
        Registers a job.
        schedule_type can be: daily | weekly | monthly | event_driven
        """
        self.jobs[name] = {
            "schedule_type": schedule_type,
            "callback": callback,
            "last_run": 0.0
        }
        logger.info(f"[Scheduler] Registered '{schedule_type}' job: {name}")

    def run_periodic_jobs(self, schedule_type: str, *args: Any, **kwargs: Any) -> int:
        """
        Triggers all jobs registered under the given schedule type (daily/weekly/monthly).
        """
        triggered_count = 0
        for name, job in self.jobs.items():
            if job["schedule_type"] == schedule_type:
                try:
                    logger.info(f"[Scheduler] Executing periodic job: {name}")
                    job["callback"](*args, **kwargs)
                    job["last_run"] = time.time()
                    self.execution_log.append({
                        "job_name": name,
                        "schedule_type": schedule_type,
                        "timestamp": time.time(),
                        "status": "success"
                    })
                    triggered_count += 1
                except Exception as e:
                    logger.error(f"[Scheduler] Job {name} failed: {e}")
                    self.execution_log.append({
                        "job_name": name,
                        "schedule_type": schedule_type,
                        "timestamp": time.time(),
                        "status": f"failed: {e}"
                    })
        return triggered_count

    def trigger_event(self, event_name: str, *args: Any, **kwargs: Any) -> int:
        """
        Triggers all event-driven jobs matching the target name/pattern.
        """
        triggered_count = 0
        for name, job in self.jobs.items():
            if job["schedule_type"] == "event_driven" and (event_name in name or name == event_name):
                try:
                    logger.info(f"[Scheduler] Executing event job: {name} on trigger: {event_name}")
                    job["callback"](*args, **kwargs)
                    job["last_run"] = time.time()
                    self.execution_log.append({
                        "job_name": name,
                        "schedule_type": "event_driven",
                        "event_name": event_name,
                        "timestamp": time.time(),
                        "status": "success"
                    })
                    triggered_count += 1
                except Exception as e:
                    logger.error(f"[Scheduler] Event job {name} failed: {e}")
                    self.execution_log.append({
                        "job_name": name,
                        "schedule_type": "event_driven",
                        "event_name": event_name,
                        "timestamp": time.time(),
                        "status": f"failed: {e}"
                    })
        return triggered_count
