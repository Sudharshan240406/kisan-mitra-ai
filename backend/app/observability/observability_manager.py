import os
import sys
import time
from typing import Any, Dict, List, Optional

from .health_engine import HealthEngine
from .logging_engine import StructuredLoggingEngine
from .metrics_engine import MetricsEngine
from .monitoring_engine import MonitoringEngine
from .tracing_engine import TracingEngine


class ObservabilityManager:
    """
    Unified manager orchestrating metrics, tracing, logging, health check queries,
    and alert monitoring. Binds as wildcard listener on the platform EventBus.
    """
    def __init__(self, container: Any) -> None:
        self.container = container
        self.metrics_engine = MetricsEngine()
        self.tracing_engine = TracingEngine()
        self.logging_engine = StructuredLoggingEngine()
        self.health_engine = HealthEngine(container)
        self.monitoring_engine = MonitoringEngine(self)

        # Register event bus wildcard subscription if available
        if hasattr(container, "event_bus") and container.event_bus:
            container.event_bus.subscribe("*", self.handle_event_bus_event)

    def handle_event_bus_event(self, event: Any) -> None:
        """
        Wildcard listener callback for the EventBus. Matches specific event types
        and triggers metrics updates or alerts.
        """
        # 1. Match AI completions
        if event.event_type == "AIRequestCompleted":
            latency = event.payload.get("latency_ms", 0.0)
            self.metrics_engine.record("llm_latency", latency, {"model_id": event.payload.get("model_id")})

            # Run confidence limits if reasoning or optimizer completes
            # Check alert rules for high latency
            self.monitoring_engine.check_alert_rules(
                event_type="ai_request",
                trace_id=event.trace_id,
                execution_id=event.request_id,
                metadata={"latency_ms": latency, "success": True}
            )

        elif event.event_type == "AIRequestFailed":
            self.monitoring_engine.check_alert_rules(
                event_type="external_api_failure",
                trace_id=event.trace_id,
                execution_id=event.request_id,
                metadata={"integration_id": event.payload.get("model_id", "Gemini"), "error": event.payload.get("error", ""), "success": False}
            )

        # 2. Match Integration / External API Failures
        elif event.event_type == "IntegrationFailed":
            self.monitoring_engine.check_alert_rules(
                event_type="IntegrationFailed",
                trace_id=event.trace_id,
                execution_id=event.request_id,
                metadata={
                    "integration_id": event.payload.get("integration_id", "Unknown"),
                    "error": event.payload.get("error", "Unknown error"),
                    "success": False
                }
            )

    # Performance Dashboard APIs
    def metrics(self) -> Dict[str, Any]:
        """
        Aggregated Metrics API.
        """
        return self.metrics_engine.get_metrics()

    async def health(self) -> Dict[str, Any]:
        """
        Subsystem Health Audit API.
        """
        return await self.health_engine.check_health()

    def traces(self) -> List[Dict[str, Any]]:
        """
        Distributed Tracing Graph API.
        """
        return self.tracing_engine.get_traces()

    def system_status(self) -> Dict[str, Any]:
        """
        CPU / Memory Diagnostics API.
        """
        stats: Dict[str, Any] = {
            "status": "online",
            "pid": os.getpid(),
            "cpu_percent": 0.0,
            "memory_usage_mb": 0.0,
            "platform": sys.platform,
            "python_version": sys.version,
            "timestamp": time.time()
        }

        try:
            import psutil
            proc = psutil.Process(os.getpid())
            stats["cpu_percent"] = round(proc.cpu_percent(interval=None), 2)
            stats["memory_usage_mb"] = round(proc.memory_info().rss / (1024 * 1024), 2)
        except ImportError:
            # Fallback for systems without psutil
            try:
                times = os.times()
                stats["cpu_percent"] = round(times.user + times.system, 2)
            except Exception:
                pass

        return stats

    def record_execution(
        self,
        event_type: str,
        trace_id: str,
        execution_id: str,
        agent: Optional[str],
        latency_ms: float,
        error: Optional[str] = None,
        confidence: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        High-level helper to record metrics, logs, and run alert rules.
        """
        metric_meta = {"agent": agent} if agent else {}
        if metadata:
            metric_meta.update(metadata)

        if agent:
            self.metrics_engine.record("agent_latency", latency_ms, {"agent": agent})
        else:
            self.metrics_engine.record("api_latency", latency_ms)

        if confidence is not None:
            self.metrics_engine.record("confidence", confidence)

        self.logging_engine.log(
            level=40 if error else 20,
            message=f"Execution recorded for {agent or 'API'}",
            trace_id=trace_id,
            execution_id=execution_id,
            agent=agent,
            latency_ms=latency_ms,
            error=error,
            confidence=confidence,
            extra=metadata
        )

        alert_meta = {
            "latency_ms": latency_ms,
            "success": error is None,
            "agent_name": agent or "API",
            "error": error,
            "confidence": confidence
        }
        self.monitoring_engine.check_alert_rules(
            event_type=event_type,
            trace_id=trace_id,
            execution_id=execution_id,
            metadata=alert_meta
        )

    def clear(self) -> None:
        """Resets the state of all inner engines."""
        self.metrics_engine.clear()
        self.tracing_engine.clear()
        self.logging_engine.clear()
        self.monitoring_engine.clear()
