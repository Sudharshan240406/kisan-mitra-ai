import logging
from typing import Optional

from app.core.ai.registry import AIProviderRegistry, ModelSpecs

logger = logging.getLogger("kisan_mitra_ai.ai.router")

class AIModelRouter:
    """
    Intelligent Model Router and Selection Engine.
    Uses Multi-Criteria Decision Analysis (MCDA) to evaluate and resolve the optimal model
    based on task types, budget constraints, prompt sizes, and system availability profiles.
    """
    def __init__(self, registry: AIProviderRegistry) -> None:
        self.registry = registry

    def select_model(
        self,
        task_type: str,
        prompt_size: int,
        budget_remaining: float,
        preferred_provider: Optional[str] = None
    ) -> tuple[str, str, float]:
        """
        Selects the best model ID using task priority and cost-aware utility scoring.
        Returns:
            tuple[model_id, selection_reason, confidence_score]
        """
        logger.info(
            f"[Selection Engine] Resolving model for task: '{task_type}' | "
            f"Prompt size: {prompt_size} chars | Budget left: ${budget_remaining:.4f}"
        )

        healthy_models = [
            m for m in self.registry.list_models()
            if m.status == "active" and m.availability == "healthy"
        ]

        if not healthy_models:
            # Absolute fallback if everything is flagged degraded/offline
            return ("llama3", "Fallback to local default due to global provider outage.", 0.2)

        # 1. Filter by Capability match
        capable_models = [m for m in healthy_models if task_type in m.capabilities]
        if not capable_models:
            logger.warning(f"No models registered with exact capability '{task_type}'. Widening search.")
            capable_models = healthy_models  # Widened default search scope

        # 2. Multi-Criteria Utility Evaluation
        best_model: Optional[ModelSpecs] = None
        best_score = -1.0
        reason = ""

        # Max input cost reference for normalization
        max_cost = max([m.cost_per_million_input for m in capable_models]) if capable_models else 1.0
        if max_cost == 0.0:
            max_cost = 1.0

        for model in capable_models:
            # Estimate input cost
            est_cost = (prompt_size / 1_000_000.0) * (model.cost_per_million_input + model.cost_per_million_output)

            # Skip if cost violates budget ceiling limits
            if est_cost > budget_remaining and model.cost_per_million_input > 0.0:
                continue

            # Determine weights dynamically based on task severity
            if task_type in ["reasoning", "planning", "verification"]:
                capability_weight = 0.7
                cost_weight = 0.2
                latency_weight = 0.1
            else:  # Simple translation or general advisory response tasks
                capability_weight = 0.2
                cost_weight = 0.6
                latency_weight = 0.2

            # Model Quality Rating (0.0 to 1.0)
            if model.model_id in ["gemini-1.5-pro", "gpt-4o", "claude-3-5-sonnet-latest"]:
                quality_score = 0.95
            elif "groq" in model.model_id:
                quality_score = 0.75
            else:  # Local/low-latency mock/llama models
                quality_score = 0.50

            # Cost Utility (cheaper models get higher score)
            cost_score = 1.0 - (model.cost_per_million_input / max_cost)

            # Latency Utility (faster models get higher score)
            latency_score = 1000.0 / max(model.average_latency_ms, 100.0)
            latency_score = min(latency_score, 1.0)

            # Preference Bonus
            pref_bonus = 0.1 if preferred_provider and model.provider_name == preferred_provider.lower() else 0.0

            # Final utility scorecard assembly
            utility_score = (
                (quality_score * capability_weight) +
                (cost_score * cost_weight) +
                (latency_score * latency_weight) +
                pref_bonus
            )

            if utility_score > best_score:
                best_score = utility_score
                best_model = model

        if best_model:
            reason = (
                f"Selected '{best_model.model_id}' (utility: {best_score:.2f}) "
                f"optimizing cost (${best_model.cost_per_million_input}/1M) and capability validation."
            )
            return (best_model.model_id, reason, round(min(best_score, 1.0), 2))

        # 3. Fallback to cheapest active model if budget checks failed on cloud models
        cheapest_model = min(capable_models, key=lambda m: m.cost_per_million_input)
        reason = f"Cheapest available model '{cheapest_model.model_id}' selected due to budget constraint bounds."
        return (cheapest_model.model_id, reason, 0.4)

    def get_fallbacks(self, primary_model_id: str) -> list[str]:
        """
        Determines the cascading list of fallback model IDs in priority order.
        """
        models = self.registry.list_models()
        # Exclude the primary model, order other models by capabilities and cost
        fallbacks = []
        for m in models:
            if m.model_id != primary_model_id and m.status == "active" and m.availability == "healthy":
                fallbacks.append(m.model_id)

        # Simple sorting: cheaper/healthy providers first in fallbacks
        def sort_key(name: str) -> float:
            specs = self.registry.get_specs(name)
            return specs.cost_per_million_input if specs else 0.0

        fallbacks.sort(key=sort_key)
        return fallbacks
