import logging
import time
from collections.abc import Generator
from typing import Any, Optional

from app.core.ai.base import AIPlatformException, NormalizedAIResponse
from app.core.ai.cost_manager import CostAndPerformanceManager
from app.core.ai.registry import AIProviderRegistry
from app.core.ai.router import AIModelRouter
from app.core.event_bus import Event, EventBus
from app.core.llm_provider import BaseLLMProvider
from app.core.logging_config import request_id_var, session_id_var, trace_id_var
from app.core.telemetry import TelemetryFramework

logger = logging.getLogger("kisan_mitra_ai.ai.platform")

class AIModelPlatform(BaseLLMProvider):
    """
    Unified AI Model Platform.
    Implements BaseLLMProvider to act as a drop-in replacement across all worker agents,
    orchestrating model selections, fallback loops, cost accounting, and events telemetry.
    """
    def __init__(
        self,
        registry: AIProviderRegistry,
        cost_manager: CostAndPerformanceManager,
        router: AIModelRouter,
        event_bus: EventBus,
        telemetry: TelemetryFramework
    ) -> None:
        self.registry = registry
        self.cost_manager = cost_manager
        self.router = router
        self.event_bus = event_bus
        self.telemetry = telemetry
        self.default_model_id = "gemini-1.5-pro"

    def get_model_name(self) -> str:
        """Returns the currently active default model name."""
        return self.default_model_id

    def _publish_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Helper to create and publish a standard platform Event with trace context."""
        try:
            event = Event(
                event_type=event_type,
                trace_id=trace_id_var.get() or "N/A",
                request_id=request_id_var.get() or "N/A",
                session_id=session_id_var.get() or "N/A",
                payload=payload
            )
            self.event_bus.publish(event)
        except Exception as e:
            logger.error(f"Failed to publish event {event_type} on EventBus: {e}")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
    ) -> str:
        # Determine task type dynamically from context or arguments
        task_type = kwargs.get("task_type", "advisory")
        preferred_provider = kwargs.get("preferred_provider", None)

        budget_left = self.cost_manager.daily_budget_usd - self.cost_manager.accumulated_cost_usd

        # 1. Selection Engine resolves primary model ID
        model_id, reason, _ = self.router.select_model(
            task_type=task_type,
            prompt_size=len(prompt),
            budget_remaining=budget_left,
            preferred_provider=preferred_provider
        )

        logger.info(f"[AI Platform] Dynamic selection resolved: {model_id} (Reason: {reason})")

        # 2. Check budget bounds before execution
        self.cost_manager.check_budget_limits(model_id, len(prompt))

        # 3. Publish AI request start trace to Event Bus
        self._publish_event(
            "AIRequestStarted",
            {
                "model_id": model_id,
                "task_type": task_type,
                "prompt_length": len(prompt),
                "timestamp": time.time()
            }
        )

        # 4. Cascade execution through fallbacks if primary fails
        models_to_try = [model_id, *self.router.get_fallbacks(model_id)]
        last_error = None

        for idx, target_model in enumerate(models_to_try):
            adapter = self.registry.get_adapter(target_model)
            if not adapter:
                logger.warning(f"No adapter registered for target model ID: {target_model}. Skipping.")
                continue

            if idx > 0:
                logger.warning(f"[AI Platform] Primary failed. Cascading fallback to: {target_model}")
                self._publish_event(
                    "AIFallbackTriggered",
                    {
                        "original_model_id": model_id,
                        "fallback_model_id": target_model,
                        "retry_index": idx,
                        "timestamp": time.time()
                    }
                )

            try:
                start_time = time.time()
                response: NormalizedAIResponse = adapter.generate(
                    prompt=prompt,
                    system_instruction=system_instruction,
                    temperature=temperature
                )
                latency_ms = (time.time() - start_time) * 1000.0

                # Enforce latency tracking
                response.latency_ms = latency_ms

                # 5. Account for actual tokens and monetary costs
                cost = self.cost_manager.record_usage(
                    model_id=target_model,
                    input_tokens=response.prompt_tokens,
                    output_tokens=response.completion_tokens
                )
                response.cost = cost

                # 6. Publish request success metrics to Event Bus
                self._publish_event(
                    "AIRequestCompleted",
                    {
                        "model_id": target_model,
                        "cost": cost,
                        "latency_ms": latency_ms,
                        "prompt_tokens": response.prompt_tokens,
                        "completion_tokens": response.completion_tokens,
                        "timestamp": time.time()
                    }
                )

                # 7. Expose metrics telemetry parameters
                self._record_telemetry(target_model, response, is_fallback=(idx > 0))

                return response.content

            except Exception as e:
                logger.error(f"Adapter execution failed for '{target_model}': {e}")
                self.cost_manager.record_error()
                last_error = e

        # If all fallback models failed
        self._publish_event(
            "AIRequestFailed",
            {
                "model_id": model_id,
                "error": str(last_error),
                "timestamp": time.time()
            }
        )
        raise AIPlatformException(f"AI Model Platform failed to resolve query across all fallback options. Last Error: {last_error}")

    def generate_stream(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs: Any
    ) -> Generator[str, None, None]:
        """
        Streams response chunks while capturing output characters to audit tokens.
        """
        task_type = kwargs.get("task_type", "advisory")
        budget_left = self.cost_manager.daily_budget_usd - self.cost_manager.accumulated_cost_usd

        model_id, _, _ = self.router.select_model(task_type, len(prompt), budget_left)
        adapter = self.registry.get_adapter(model_id)

        if not adapter:
            adapter = self.registry.get_adapter("llama3")  # Local default fallback

        assert adapter is not None

        accumulated_chunks = []
        start_time = time.time()

        try:
            for chunk in adapter.generate_stream(prompt, system_instruction, temperature):
                accumulated_chunks.append(chunk)
                yield chunk
        finally:
            # End of stream hook: perform telemetry accounting
            final_text = "".join(accumulated_chunks)
            latency_ms = (time.time() - start_time) * 1000.0

            p_tokens = len(prompt) // 4
            c_tokens = len(final_text) // 4

            cost = self.cost_manager.record_usage(model_id, p_tokens, c_tokens)

            # Record stream metadata to telemetry
            dummy_response = NormalizedAIResponse(
                content=final_text,
                model_name=model_id,
                provider_name="adapter",
                prompt_tokens=p_tokens,
                completion_tokens=c_tokens,
                cost=cost,
                latency_ms=latency_ms
            )
            self._record_telemetry(model_id, dummy_response, is_fallback=False)

    def _record_telemetry(self, model_id: str, response: NormalizedAIResponse, is_fallback: bool) -> None:
        """
        Pushes AI Platform metrics parameters to the telemetry framework.
        """
        self.telemetry.record(
            name="ai_tokens_count",
            value=response.prompt_tokens + response.completion_tokens,
            trace_id="N/A",
            session_id="N/A",
            metadata={
                "model_id": model_id,
                "input_tokens": response.prompt_tokens,
                "output_tokens": response.completion_tokens,
                "cost": response.cost,
                "latency_ms": response.latency_ms,
                "is_fallback": is_fallback
            }
        )
        self.telemetry.record(
            name="ai_execution_cost_usd",
            value=response.cost,
            trace_id="N/A",
            session_id="N/A",
            metadata={"model_id": model_id}
        )
        self.telemetry.record(
            name="ai_execution_latency_ms",
            value=response.latency_ms,
            trace_id="N/A",
            session_id="N/A",
            metadata={"model_id": model_id}
        )
