import time
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class Alert(BaseModel):
    id: str
    timestamp: float = Field(default_factory=time.time)
    rule_name: str
    severity: str  # warning, critical
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MonitoringEngine:
    """
    Monitors engine events, performance limits, and executes alerting rules:
    - High latency detection (> 5000ms)
    - Repeated agent/service failures (>= 3 consecutive failures)
    - Agent crashes
    - External API / Integration failures
    - Low confidence spikes (< 0.5 for consecutive calls)
    """
    def __init__(self, manager: Any) -> None:
        self.manager = manager
        self.alerts: List[Alert] = []
        self._consecutive_failures: Dict[str, int] = {}
        self._consecutive_low_confidence: int = 0

    def check_alert_rules(
        self,
        event_type: str,
        trace_id: str,
        execution_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Runs alert rules against recorded execution metrics.
        """
        # 1. High Latency Detection
        if "latency_ms" in metadata:
            lat = metadata["latency_ms"]
            if lat > 5000:
                self.raise_alert(
                    rule_name="High Latency",
                    severity="warning",
                    message=f"Request took {lat:.1f}ms, exceeding threshold of 5000ms",
                    metadata={"trace_id": trace_id, "execution_id": execution_id, "latency_ms": lat}
                )

        # 2. Agent Crash / Failure Detection
        if event_type == "agent_failure":
            agent_name = metadata.get("agent_name", "Unknown")
            error_msg = metadata.get("error", "Unknown error")
            self.raise_alert(
                rule_name="Agent Crash",
                severity="critical",
                message=f"Agent '{agent_name}' crashed: {error_msg}",
                metadata={"trace_id": trace_id, "execution_id": execution_id, "agent_name": agent_name, "error": error_msg}
            )

        # 3. Repeated Failures
        if "success" in metadata:
            success = metadata["success"]
            agent_name = metadata.get("agent_name", "system")
            if not success:
                self._consecutive_failures[agent_name] = self._consecutive_failures.get(agent_name, 0) + 1
                if self._consecutive_failures[agent_name] >= 3:
                    self.raise_alert(
                        rule_name="Repeated Failures",
                        severity="critical",
                        message=f"Agent/System '{agent_name}' failed {self._consecutive_failures[agent_name]} times consecutively.",
                        metadata={"trace_id": trace_id, "agent_name": agent_name}
                    )
            else:
                self._consecutive_failures[agent_name] = 0

        # 4. External API Failure Detection
        if event_type in ("external_api_failure", "IntegrationFailed"):
            api_name = metadata.get("api_name", metadata.get("integration_id", "Unknown"))
            error = metadata.get("error", "")
            self.raise_alert(
                rule_name="External API Failure",
                severity="critical",
                message=f"External API '{api_name}' failed: {error}",
                metadata={"trace_id": trace_id, "api_name": api_name, "error": error}
            )

        # 5. Low Confidence Spike Detection
        if "confidence" in metadata:
            conf = metadata["confidence"]
            if conf is not None and conf < 0.5:
                self._consecutive_low_confidence += 1
                if self._consecutive_low_confidence >= 3:
                    self.raise_alert(
                        rule_name="Low Confidence Spike",
                        severity="warning",
                        message=f"Confidence has been low (< 0.5) for {self._consecutive_low_confidence} consecutive requests.",
                        metadata={"trace_id": trace_id, "confidence": conf}
                    )
            else:
                self._consecutive_low_confidence = 0

    def raise_alert(self, rule_name: str, severity: str, message: str, metadata: Dict[str, Any]) -> None:
        """
        Creates and stores an alert, and logs it structured as well.
        """
        alert_id = f"alt-{int(time.time())}-{len(self.alerts)}"
        alert = Alert(id=alert_id, rule_name=rule_name, severity=severity, message=message, metadata=metadata)
        self.alerts.append(alert)

        # Log alert to structured logging engine
        self.manager.logging_engine.log(
            level=30 if severity == "warning" else 40,
            message=f"ALERT [{rule_name}]: {message}",
            trace_id=metadata.get("trace_id", "N/A"),
            execution_id=metadata.get("execution_id", "N/A"),
            agent=metadata.get("agent_name"),
            latency_ms=metadata.get("latency_ms"),
            error=metadata.get("error"),
            confidence=metadata.get("confidence")
        )

    def get_alerts(self) -> List[Dict[str, Any]]:
        """Returns all raised alerts."""
        return [alert.model_dump() for alert in self.alerts]

    def clear(self) -> None:
        """Resets raised alerts and counters."""
        self.alerts.clear()
        self._consecutive_failures.clear()
        self._consecutive_low_confidence = 0
