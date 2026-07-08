import logging
import time
from typing import Any, Dict, List

logger = logging.getLogger("kisan_mitra_ai.workflows.retry")

class RetryEngine:
    """
    Manages exponential backoff scheduling, dead-letter queue routing, and failure logs.
    """
    def __init__(self, obs_mgr: Any = None) -> None:
        self.obs_mgr = obs_mgr
        self.dlq: List[Dict[str, Any]] = []
        self.failure_log: List[Dict[str, Any]] = []

    def get_failure_rate(self) -> float:
        """
        Calculates current failure rate.
        """
        if not self.failure_log:
            return 0.0
        failures = sum(1 for f in self.failure_log if f.get("status") == "failed")
        return failures / len(self.failure_log)

    def log_failure(self, entity_id: str, error: str, category: str) -> None:
        """
        Tracks a task/job failure event.
        """
        self.failure_log.append({
            "entity_id": entity_id,
            "error": error,
            "category": category,
            "timestamp": time.time()
        })
        if self.obs_mgr:
            self.obs_mgr.metrics_engine.record("failed_jobs", 1, {"category": category})

    def move_to_dlq(self, entity_id: str, payload: Any, error: str, category: str) -> None:
        """
        Pushes a persistently failing task/job into the Dead-Letter Queue (DLQ).
        """
        logger.error(f"[RetryEngine] Moving {category} '{entity_id}' to Dead-Letter Queue. Error: {error}")
        self.dlq.append({
            "entity_id": entity_id,
            "payload": payload,
            "error": error,
            "category": category,
            "timestamp": time.time()
        })
