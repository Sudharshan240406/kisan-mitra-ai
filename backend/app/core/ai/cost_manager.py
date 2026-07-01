import logging
from typing import Any

from app.core.ai.base import AICostLimitExceeded
from app.core.ai.registry import AIProviderRegistry

logger = logging.getLogger("kisan_mitra_ai.ai.cost_manager")

class CostAndPerformanceManager:
    """
    Manages monetary expenses and token throughput metrics of AI model invocations.
    Enforces daily safety thresholds.
    """
    def __init__(self, registry: AIProviderRegistry, daily_budget_usd: float = 5.0) -> None:
        self.registry = registry
        self.daily_budget_usd = daily_budget_usd

        # Accumulators
        self.accumulated_input_tokens = 0
        self.accumulated_output_tokens = 0
        self.accumulated_cost_usd = 0.0
        self.error_count = 0
        self.requests_count = 0

    def calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculates the estimated monetary cost in USD of a query execution.
        """
        specs = self.registry.get_specs(model_id)
        if not specs:
            return 0.0

        cost_in = (input_tokens / 1_000_000.0) * specs.cost_per_million_input
        cost_out = (output_tokens / 1_000_000.0) * specs.cost_per_million_output
        return round(cost_in + cost_out, 6)

    def record_usage(self, model_id: str, input_tokens: int, output_tokens: int) -> float:
        """
        Records actual usage and increments overall ledger accumulators.
        """
        cost = self.calculate_cost(model_id, input_tokens, output_tokens)
        self.accumulated_input_tokens += input_tokens
        self.accumulated_output_tokens += output_tokens
        self.accumulated_cost_usd += cost
        self.requests_count += 1

        logger.info(
            f"[Cost Manager] Recorded: {model_id} | Input: {input_tokens}t | Output: {output_tokens}t | "
            f"Cost: ${cost:.6f} | Total Cost: ${self.accumulated_cost_usd:.4f}"
        )
        return cost

    def check_budget_limits(self, model_id: str, estimated_input_tokens: int) -> None:
        """
        Guards execution. Throws exception if transaction cost exceeds budget caps.
        """
        # Estimate input cost, assume output matches input length for security margin
        cost = self.calculate_cost(model_id, estimated_input_tokens, estimated_input_tokens)
        projected_total = self.accumulated_cost_usd + cost

        if projected_total > self.daily_budget_usd:
            raise AICostLimitExceeded(
                f"Execution blocked. Projected cost of ${cost:.4f} pushes overall spend to "
                f"${projected_total:.4f}, exceeding configured daily budget cap of ${self.daily_budget_usd:.2f}."
            )

    def record_error(self) -> None:
        """Increments system request error statistics."""
        self.error_count += 1

    def get_summary(self) -> dict[str, Any]:
        """Compiles cost summaries for telemetry reports."""
        return {
            "total_requests": self.requests_count,
            "total_errors": self.error_count,
            "success_rate": (self.requests_count - self.error_count) / self.requests_count if self.requests_count > 0 else 1.0,
            "accumulated_input_tokens": self.accumulated_input_tokens,
            "accumulated_output_tokens": self.accumulated_output_tokens,
            "accumulated_cost_usd": round(self.accumulated_cost_usd, 6),
            "daily_budget_usd": self.daily_budget_usd,
            "budget_utilization_percent": round((self.accumulated_cost_usd / self.daily_budget_usd) * 100.0, 2) if self.daily_budget_usd > 0 else 0.0
        }

    def reset_totals(self) -> None:
        """Resets the budget ledger (e.g. at daily schedule trigger)."""
        self.accumulated_input_tokens = 0
        self.accumulated_output_tokens = 0
        self.accumulated_cost_usd = 0.0
        self.error_count = 0
        self.requests_count = 0
        logger.info("[Cost Manager] Ledger statistics reset successfully.")
