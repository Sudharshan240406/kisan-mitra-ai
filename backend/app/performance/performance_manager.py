import logging
import time
from typing import Any, Dict, List

from .cache_engine import CacheEngine
from .concurrency_manager import ConcurrencyManager
from .rate_limiter import RateLimiter
from .resource_pool import ResourcePool

logger = logging.getLogger("kisan_mitra_ai.performance.manager")

class PerformanceManager:
    """
    Central performance orchestration manager instantiating core resource pools and tracking telemetry.
    """
    def __init__(self, container: Any = None) -> None:
        self.container = container

        # 1. Caches (Task 2)
        self.memory_cache = CacheEngine(default_ttl=300.0)
        self.knowledge_cache = CacheEngine(default_ttl=300.0)
        self.embedding_cache = CacheEngine(default_ttl=300.0)
        self.prediction_cache = CacheEngine(default_ttl=300.0)

        # 2. Concurrency Coordinator (Task 4)
        self.concurrency_manager = ConcurrencyManager()

        # 3. Rate Throttler (Task 5)
        self.rate_limiter = RateLimiter(capacity=25, refill_rate=5.0)

        # 4. Mock Client Resource Pools (Task 3)
        self.llm_pool = ResourcePool(factory=lambda: "mock_llm_client", max_size=10)
        self.vector_pool = ResourcePool(factory=lambda: "mock_vector_client", max_size=10)
        self.db_pool = ResourcePool(factory=lambda: "mock_db_connection", max_size=10)
        self.http_pool = ResourcePool(factory=lambda: "mock_http_client", max_size=10)

        # 5. Telemetry State variables
        self.latencies: List[float] = []
        self.throughput_count = 0
        self.start_time = time.time()

    def record_latency(self, latency_ms: float) -> None:
        """
        Logs query latencies to profile average and peak performance.
        """
        self.latencies.append(latency_ms)
        self.throughput_count += 1

        obs_mgr = getattr(self.container, "observability_manager", None)
        if obs_mgr:
            obs_mgr.metrics_engine.record("average_latency", latency_ms)
            obs_mgr.metrics_engine.record("throughput", float(self.throughput_count))

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Aggregates performance benchmarks and hit ratios.
        """
        avg_lat = sum(self.latencies) / len(self.latencies) if self.latencies else 0.0
        peak_lat = max(self.latencies) if self.latencies else 0.0

        # Cache Hit Ratios
        total_cache_hits = (
            self.memory_cache._hits +
            self.knowledge_cache._hits +
            self.embedding_cache._hits +
            self.prediction_cache._hits
        )
        total_cache_misses = (
            self.memory_cache._misses +
            self.knowledge_cache._misses +
            self.embedding_cache._misses +
            self.prediction_cache._misses
        )
        total_accesses = total_cache_hits + total_cache_misses
        hit_ratio = total_cache_hits / total_accesses if total_accesses > 0 else 0.0

        # Queue depth and worker utilization simulation
        queue_util = 0.0
        worker_util = 0.0
        if hasattr(self.container, "workflow_manager") and self.container.workflow_manager:
            qm = self.container.workflow_manager.queue_manager
            queue_util = float(qm.get_queue_depth())

            # Simple simulation check of running workers
            if hasattr(self.container.workflow_manager, "job_runner"):
                worker_util = 0.75 if self.container.workflow_manager.job_runner._workers else 0.0

        return {
            "cache_hit_ratio": round(hit_ratio, 4),
            "throughput": float(self.throughput_count),
            "average_latency_ms": round(avg_lat, 2),
            "peak_latency_ms": round(peak_lat, 2),
            "queue_utilization": queue_util,
            "worker_utilization": worker_util,
            "pools": {
                "llm": self.llm_pool.get_utilization(),
                "vector": self.vector_pool.get_utilization(),
                "db": self.db_pool.get_utilization(),
                "http": self.http_pool.get_utilization(),
            }
        }
