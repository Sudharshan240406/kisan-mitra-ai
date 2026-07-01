import logging
from typing import Any, Optional

from app.core.telemetry import TelemetryFramework

logger = logging.getLogger("kisan_mitra_ai.knowledge.telemetry")


class KnowledgeTelemetry:
    """
    Observer class tracking query performance and exporting metric values into the central Telemetry Framework.
    """
    def __init__(self, telemetry_framework: Optional[TelemetryFramework] = None) -> None:
        self.telemetry = telemetry_framework
        self.query_count = 0
        self.total_latency_ms = 0.0

    def record_query(
        self,
        query: str,
        latency_ms: float,
        results_count: int,
        cache_hit: bool,
        trace_id: str,
        session_id: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Logs and records query retrieval execution times and caching counts.
        """
        self.query_count += 1
        self.total_latency_ms += latency_ms

        logger.info(
            f"Knowledge Query Telemetry: Query='{query}' | Latency={latency_ms:.2f}ms | "
            f"Results={results_count} | CacheHit={cache_hit}"
        )

        if self.telemetry:
            # Record query latency
            self.telemetry.record(
                name="knowledge_query_latency_ms",
                value=latency_ms,
                trace_id=trace_id,
                session_id=session_id,
                metadata={
                    "query": query,
                    "results_count": results_count,
                    "cache_hit": cache_hit,
                    **(metadata or {})
                }
            )

            # Record cache status
            self.telemetry.record(
                name="knowledge_cache_hit",
                value=1 if cache_hit else 0,
                trace_id=trace_id,
                session_id=session_id,
                metadata={"query": query}
            )

            # Record result metrics
            self.telemetry.record(
                name="knowledge_results_count",
                value=results_count,
                trace_id=trace_id,
                session_id=session_id,
                metadata={"query": query}
            )

    @property
    def statistics(self) -> dict[str, Any]:
        avg_latency = self.total_latency_ms / self.query_count if self.query_count > 0 else 0.0
        return {
            "total_queries": self.query_count,
            "average_latency_ms": round(avg_latency, 2),
            "total_latency_ms": round(self.total_latency_ms, 2)
        }
