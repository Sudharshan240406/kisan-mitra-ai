import logging
import time
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai")

class MetricEntry(BaseModel):
    """
    Individual metrics record entry.
    """
    timestamp: float = Field(default_factory=time.time)
    metric_name: str
    value: Any
    trace_id: str
    session_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class MetricsCollector:
    """
    Centralized in-memory metrics store designed to collect telemetry data
    for agent executions, token usage, tool invocations, and warnings.
    """
    def __init__(self) -> None:
        self._entries: list[MetricEntry] = []
        self._aggregate_tokens: int = 0
        self._tool_calls_tally: dict[str, int] = {}
        self._errors_count: int = 0
        self._retries_count: int = 0
        logger.info("MetricsCollector initialized.")

    def record(
        self,
        name: str,
        value: Any,
        trace_id: str,
        session_id: str,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """
        Record a telemetry metric entry.
        """
        entry = MetricEntry(
            metric_name=name,
            value=value,
            trace_id=trace_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        self._entries.append(entry)

        # Keep quick local aggregates
        if name == "token_usage" and isinstance(value, int):
            self._aggregate_tokens += value
        elif name == "tool_call" and isinstance(value, str):
            self._tool_calls_tally[value] = self._tool_calls_tally.get(value, 0) + 1
        elif name == "error":
            self._errors_count += 1
        elif name == "retry":
            self._retries_count += 1

    def get_aggregated_stats(self) -> dict[str, Any]:
        """
        Retrieve a summary summary of metrics logs.
        """
        return {
            "total_records": len(self._entries),
            "accumulated_tokens": self._aggregate_tokens,
            "tool_calls_breakdown": self._tool_calls_tally,
            "total_errors_recorded": self._errors_count,
            "total_retries_recorded": self._retries_count
        }

    def get_trace_metrics(self, trace_id: str) -> list[MetricEntry]:
        """
        Get all metric entries matching a specific request trace ID.
        """
        return [entry for entry in self._entries if entry.trace_id == trace_id]

    def health(self) -> dict[str, Any]:
        """
        Exposes health metrics for the collector.
        """
        return {
            "status": "healthy",
            "metrics_count": len(self._entries),
            "aggregate_tokens": self._aggregate_tokens
        }
