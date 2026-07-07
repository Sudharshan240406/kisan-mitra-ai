import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetricPoint(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    name: str
    value: float
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MetricsEngine:
    """
    Collects, aggregates, and retrieves application latency metrics
    including API, Agent, LLM, Memory, Knowledge, Prediction, and Notification latency.
    """
    def __init__(self) -> None:
        self._metrics: Dict[str, List[MetricPoint]] = {}

    def record(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Records a single measurement point for a given metric name.
        """
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(MetricPoint(name=name, value=value, metadata=metadata or {}))

    def get_metrics(self) -> Dict[str, Any]:
        """
        Aggregates and returns summary statistics for each tracked metric.
        """
        result: Dict[str, Any] = {}
        for name, points in self._metrics.items():
            if not points:
                continue
            values = [p.value for p in points]
            result[name] = {
                "count": len(values),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "avg": round(sum(values) / len(values), 2),
                "latest": round(values[-1], 2),
            }
        return result

    def clear(self) -> None:
        """
        Resets all recorded metrics.
        """
        self._metrics.clear()
