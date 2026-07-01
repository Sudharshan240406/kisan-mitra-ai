"""
Kisan Mitra AI — Reasoning Telemetry
======================================
Captures and publishes structured telemetry events for every reasoning
session. Feeds the Ops Dashboard with latency, confidence, escalation,
and evidence-count time-series metrics.

Events emitted:
  - reasoning_session_completed
  - reasoning_session_escalated
  - reasoning_session_failed
"""
from __future__ import annotations

import logging
import time
from typing import Any, Optional

logger = logging.getLogger("kisan_mitra_ai.reasoning.telemetry")


class ReasoningTelemetryEvent:
    """Structured telemetry event for a reasoning session lifecycle."""

    def __init__(
        self,
        event_type: str,
        session_id: str,
        trace_id: str,
        duration_ms: float,
        evidence_count: int,
        confidence: float,
        consensus_success: bool,
        escalated: bool,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        self.event_type = event_type
        self.session_id = session_id
        self.trace_id = trace_id
        self.timestamp = time.time()
        self.duration_ms = duration_ms
        self.evidence_count = evidence_count
        self.confidence = confidence
        self.consensus_success = consensus_success
        self.escalated = escalated
        self.metadata = metadata or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "duration_ms": round(self.duration_ms, 2),
            "evidence_count": self.evidence_count,
            "confidence": round(self.confidence, 4),
            "consensus_success": self.consensus_success,
            "escalated": self.escalated,
            "metadata": self.metadata,
        }


class ReasoningTelemetry:
    """
    Telemetry recorder for the Reasoning Platform.

    Maintains an in-memory event buffer and exposes aggregate summary
    metrics for the Ops Dashboard endpoint.
    """

    def __init__(self, max_buffer: int = 1000) -> None:
        self._events: list[ReasoningTelemetryEvent] = []
        self.max_buffer = max_buffer
        self._total_duration_ms: float = 0.0
        self._total_confidence: float = 0.0
        self._total_evidence: int = 0
        self._total_consensus_success: int = 0
        self._total_escalations: int = 0
        self._total_events: int = 0

    def record(
        self,
        session_id: str,
        trace_id: str,
        duration_ms: float,
        evidence_count: int,
        confidence: float,
        consensus_success: bool,
        escalated: bool,
        agent_context: Any = None,
    ) -> None:
        """Records a completed reasoning session telemetry event."""
        event_type = "reasoning_session_escalated" if escalated else "reasoning_session_completed"
        metadata: dict[str, Any] = {}
        if agent_context is not None:
            try:
                metadata["query_type"] = getattr(agent_context, "query_type", "unknown")
                metadata["farmer_id"] = getattr(agent_context, "farmer_id", None)
            except Exception:
                pass

        event = ReasoningTelemetryEvent(
            event_type=event_type,
            session_id=session_id,
            trace_id=trace_id,
            duration_ms=duration_ms,
            evidence_count=evidence_count,
            confidence=confidence,
            consensus_success=consensus_success,
            escalated=escalated,
            metadata=metadata,
        )
        self._events.append(event)
        if len(self._events) > self.max_buffer:
            self._events.pop(0)

        # Update running aggregates
        self._total_events += 1
        self._total_duration_ms += duration_ms
        self._total_confidence += confidence
        self._total_evidence += evidence_count
        if consensus_success:
            self._total_consensus_success += 1
        if escalated:
            self._total_escalations += 1

        logger.info(
            f"[ReasoningTelemetry] Event recorded: {event_type} "
            f"(session={session_id}, conf={confidence:.2f}, "
            f"dur={duration_ms:.1f}ms, escalated={escalated})"
        )

    def record_failure(self, session_id: str, trace_id: str, reason: str) -> None:
        """Records a failed reasoning session."""
        event = ReasoningTelemetryEvent(
            event_type="reasoning_session_failed",
            session_id=session_id,
            trace_id=trace_id,
            duration_ms=0.0,
            evidence_count=0,
            confidence=0.0,
            consensus_success=False,
            escalated=False,
            metadata={"failure_reason": reason},
        )
        self._events.append(event)
        self._total_events += 1
        logger.error(f"[ReasoningTelemetry] Session FAILED: {session_id} — {reason}")

    def aggregate_metrics(self) -> dict[str, Any]:
        """Returns aggregate metrics suitable for the Ops Dashboard."""
        n = self._total_events or 1
        return {
            "total_sessions": self._total_events,
            "avg_duration_ms": round(self._total_duration_ms / n, 2),
            "avg_confidence": round(self._total_confidence / n, 4),
            "avg_evidence_count": round(self._total_evidence / n, 1),
            "consensus_success_rate": round(self._total_consensus_success / n, 4),
            "escalation_rate": round(self._total_escalations / n, 4),
            "total_escalations": self._total_escalations,
        }

    def recent_events(self, limit: int = 20) -> list[dict[str, Any]]:
        """Returns the most recent `limit` events as serializable dicts."""
        return [e.to_dict() for e in self._events[-limit:]]

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "component": "ReasoningTelemetry",
            "buffered_events": len(self._events),
            "total_recorded": self._total_events,
        }
