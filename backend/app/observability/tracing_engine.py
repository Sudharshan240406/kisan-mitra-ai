import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Dict, Generator, List, Optional

from pydantic import BaseModel, Field

# Context propagation variables for tracing
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
execution_id_var: ContextVar[Optional[str]] = ContextVar("execution_id", default=None)

class SpanRecord(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    execution_id: str
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "success"
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TracingEngine:
    """
    Manages trace spans and allows retrieval of collected spans
    to map execution graphs and distributed tracing flows.
    """
    def __init__(self) -> None:
        self._spans: List[SpanRecord] = []

    def record_span(self, span: SpanRecord) -> None:
        """Records a completed span."""
        self._spans.append(span)

    def get_traces(self) -> List[Dict[str, Any]]:
        """Returns all recorded trace spans."""
        return [span.model_dump() for span in self._spans]

    def get_trace_by_id(self, trace_id: str) -> List[Dict[str, Any]]:
        """Retrieves spans matching a specific trace ID."""
        return [span.model_dump() for span in self._spans if span.trace_id == trace_id]

    def clear(self) -> None:
        """Clears all recorded spans."""
        self._spans.clear()

@contextmanager
def trace_span(
    name: str,
    engine: TracingEngine,
    trace_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Generator[SpanRecord, None, None]:
    """
    Context manager to trace code execution. Automatically links parent-child spans,
    measures execution duration, and registers the span with the engine.
    """
    current_trace = trace_id or trace_id_var.get() or f"tr-{uuid.uuid4().hex[:8]}"
    current_exec = execution_id or execution_id_var.get() or f"ex-{uuid.uuid4().hex[:8]}"
    parent_span = span_id_var.get()
    current_span = f"sp-{uuid.uuid4().hex[:8]}"

    # Set context variables
    token_trace = trace_id_var.set(current_trace)
    token_exec = execution_id_var.set(current_exec)
    token_span = span_id_var.set(current_span)

    span = SpanRecord(
        trace_id=current_trace,
        span_id=current_span,
        parent_span_id=parent_span,
        execution_id=current_exec,
        name=name,
        start_time=time.time(),
        metadata=metadata or {}
    )

    try:
        yield span
    except Exception as e:
        span.status = "failed"
        span.error = str(e)
        raise e
    finally:
        span.end_time = time.time()
        span.duration_ms = (span.end_time - span.start_time) * 1000.0
        engine.record_span(span)

        # Reset context variables
        trace_id_var.reset(token_trace)
        execution_id_var.reset(token_exec)
        span_id_var.reset(token_span)
