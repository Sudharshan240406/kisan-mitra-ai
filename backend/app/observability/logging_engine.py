import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger("kisan_mitra_ai.observability.structured")

class StructuredLogRecord:
    """
    Structured log entry capturing execution context metadata.
    """
    def __init__(
        self,
        message: str,
        trace_id: str,
        execution_id: str,
        agent: Optional[str] = None,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
        confidence: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        self.timestamp = datetime.utcnow().isoformat()
        self.message = message
        self.trace_id = trace_id
        self.execution_id = execution_id
        self.agent = agent
        self.latency_ms = latency_ms
        self.error = error
        self.confidence = confidence
        self.extra = extra or {}

    def to_dict(self) -> Dict[str, Any]:
        """Converts the structured log record to a dictionary."""
        res: Dict[str, Any] = {
            "timestamp": self.timestamp,
            "message": self.message,
            "trace_id": self.trace_id,
            "execution_id": self.execution_id,
            "agent": self.agent,
            "latency_ms": round(self.latency_ms, 2) if self.latency_ms is not None else None,
            "error": self.error,
            "confidence": round(self.confidence, 4) if self.confidence is not None else None,
        }
        if self.extra:
            res["extra"] = self.extra
        return res

class StructuredLoggingEngine:
    """
    Logging Engine that outputs and maintains structured JSON logs.
    """
    def __init__(self) -> None:
        self._logs: List[Dict[str, Any]] = []

    def log(
        self,
        level: int,
        message: str,
        trace_id: str,
        execution_id: str,
        agent: Optional[str] = None,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
        confidence: Optional[float] = None,
        extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Formats and records a structured JSON log entry, and forwards it to standard logging.
        """
        record = StructuredLogRecord(
            message=message,
            trace_id=trace_id,
            execution_id=execution_id,
            agent=agent,
            latency_ms=latency_ms,
            error=error,
            confidence=confidence,
            extra=extra
        )
        record_dict = record.to_dict()
        self._logs.append(record_dict)

        # Output to console / file logger as JSON string
        log_extra = {
            "trace_id": trace_id,
            "request_id": execution_id,
            "extra_fields": record_dict
        }
        logger.log(level, json.dumps(record_dict), extra=log_extra)

    def get_logs(self) -> List[Dict[str, Any]]:
        """Returns all collected structured logs."""
        return self._logs

    def clear(self) -> None:
        """Clears all stored logs."""
        self._logs.clear()
