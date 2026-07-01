import asyncio
import logging
import time
from typing import Any, Callable, Optional, TypeVar

from app.core.event_bus import Event, EventBus

logger = logging.getLogger("kisan_mitra_ai.integrations.resilience")

T = TypeVar("T")


class CircuitBreakerOpenException(Exception):
    """
    Raised when the circuit breaker is OPEN and fails fast.
    """
    pass


class CircuitBreaker:
    """
    In-memory Circuit Breaker tracking failures and handling state transitions.
    """
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 5.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.last_state_change = time.time()

    def record_success(self) -> None:
        """
        Records a successful operation and resets state.
        """
        self.failure_count = 0
        if self.state != "CLOSED":
            logger.info(f"CircuitBreaker state transition: {self.state} -> CLOSED")
            self.state = "CLOSED"
            self.last_state_change = time.time()

    def record_failure(self) -> None:
        """
        Records a failure and triggers OPEN state if threshold is exceeded.
        """
        self.failure_count += 1
        if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            logger.warning(f"CircuitBreaker state transition: CLOSED -> OPEN (failures: {self.failure_count})")
            self.state = "OPEN"
            self.last_state_change = time.time()
        elif self.state == "HALF_OPEN":
            logger.warning("CircuitBreaker state transition: HALF_OPEN -> OPEN (trial call failed)")
            self.state = "OPEN"
            self.last_state_change = time.time()

    def allow_execution(self) -> bool:
        """
        Determines whether execution is allowed or fails fast.
        """
        if self.state == "OPEN":
            if time.time() - self.last_state_change > self.recovery_timeout:
                logger.info("CircuitBreaker state transition: OPEN -> HALF_OPEN (recovery timeout passed)")
                self.state = "HALF_OPEN"
                self.last_state_change = time.time()
                return True
            return False
        return True


class ResilientRunner:
    """
    Runner coordinating retries, timeouts, fallback, and telemetry for integration calls.
    """
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        telemetry: Optional[Any] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ) -> None:
        self.event_bus = event_bus
        self.telemetry = telemetry
        self.circuit_breaker = circuit_breaker or CircuitBreaker()

    async def execute(
        self,
        integration_id: str,
        operation_name: str,
        func: Callable[[], Any],
        fallback: Optional[Callable[[], Any]] = None,
        retries: int = 3,
        backoff_factor: float = 1.5,
        timeout: float = 5.0,
        trace_id: str = "system",
        request_id: str = "system",
        session_id: str = "system"
    ) -> Any:
        """
        Executes a callable with complete fault-tolerance wrappers.
        """
        if not self.circuit_breaker.allow_execution():
            logger.warning(f"[CircuitBreaker] '{integration_id}' is OPEN. Failing fast.")
            if fallback:
                logger.info(f"[CircuitBreaker] Executing fallback for '{integration_id}'.")
                return fallback()
            raise CircuitBreakerOpenException(f"Circuit breaker for integration '{integration_id}' is OPEN.")

        if self.event_bus:
            self.event_bus.publish(Event(
                event_type="IntegrationStarted",
                trace_id=trace_id,
                request_id=request_id,
                session_id=session_id,
                payload={"integration_id": integration_id, "operation": operation_name}
            ))

        start_time = time.time()
        attempt = 0
        current_delay = 0.1

        while attempt <= retries:
            attempt_start = time.time()
            try:
                if attempt > 0:
                    if self.event_bus:
                        self.event_bus.publish(Event(
                            event_type="RetryStarted",
                            trace_id=trace_id,
                            request_id=request_id,
                            session_id=session_id,
                            payload={
                                "integration_id": integration_id,
                                "attempt": attempt,
                                "delay": current_delay
                            }
                        ))
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_factor

                # Run operation under timeout
                if asyncio.iscoroutinefunction(func):
                    result = await asyncio.wait_for(func(), timeout=timeout)
                else:
                    result = func()
                    if asyncio.iscoroutine(result):
                        result = await asyncio.wait_for(result, timeout=timeout)

                duration_ms = (time.time() - start_time) * 1000.0
                self.circuit_breaker.record_success()

                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type="IntegrationCompleted",
                        trace_id=trace_id,
                        request_id=request_id,
                        session_id=session_id,
                        payload={"integration_id": integration_id, "duration_ms": duration_ms}
                    ))
                    if attempt > 0:
                        self.event_bus.publish(Event(
                            event_type="RetryCompleted",
                            trace_id=trace_id,
                            request_id=request_id,
                            session_id=session_id,
                            payload={"integration_id": integration_id, "attempts": attempt}
                        ))

                if self.telemetry:
                    self.telemetry.record(
                        name="integration_latency_ms",
                        value=duration_ms,
                        trace_id=trace_id,
                        session_id=session_id,
                        metadata={"integration_id": integration_id, "status": "success", "attempts": attempt}
                    )

                return result

            except Exception as e:
                attempt += 1
                attempt_duration_ms = (time.time() - attempt_start) * 1000.0
                logger.warning(f"Attempt {attempt} failed for '{integration_id}': {e!s}")

                is_retryable = self._classify_error(e)
                if not is_retryable or attempt > retries:
                    # Permanent Failure
                    self.circuit_breaker.record_failure()
                    duration_ms = (time.time() - start_time) * 1000.0

                    if self.event_bus:
                        self.event_bus.publish(Event(
                            event_type="IntegrationFailed",
                            trace_id=trace_id,
                            request_id=request_id,
                            session_id=session_id,
                            payload={
                                "integration_id": integration_id,
                                "error": str(e),
                                "duration_ms": duration_ms
                            }
                        ))

                    if self.telemetry:
                        self.telemetry.record(
                            name="integration_failure",
                            value=1.0,
                            trace_id=trace_id,
                            session_id=session_id,
                            metadata={"integration_id": integration_id, "error": type(e).__name__}
                        )
                        self.telemetry.record(
                            name="integration_latency_ms",
                            value=duration_ms,
                            trace_id=trace_id,
                            session_id=session_id,
                            metadata={"integration_id": integration_id, "status": "failed", "attempts": attempt}
                        )

                    if fallback:
                        logger.info(f"Executing fallback for '{integration_id}' after failure.")
                        res = fallback()
                        if asyncio.iscoroutine(res):
                            return await res
                        return res
                    raise e

    def _classify_error(self, exc: Exception) -> bool:
        """
        Classifies an error as retryable or non-retryable.
        """
        if isinstance(exc, (ValueError, KeyError, TypeError, PermissionError, NotImplementedError, CircuitBreakerOpenException)):
            return False
        return True
