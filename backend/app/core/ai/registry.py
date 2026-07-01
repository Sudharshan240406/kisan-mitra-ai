import logging
from typing import Optional

from app.core.ai.base import IProviderAdapter
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.ai.registry")

class ModelSpecs(BaseModel):
    """
    Structured model specifications mapping pricing matrices, token bounds, and capability ratings.
    """
    model_id: str
    provider_name: str
    capabilities: list[str] = Field(default_factory=list)
    cost_per_million_input: float = 0.0  # USD per 1M input tokens
    cost_per_million_output: float = 0.0 # USD per 1M output tokens
    context_window: int = 4096
    average_latency_ms: float = 200.0
    reliability_rate: float = 0.99
    availability: str = "healthy"  # healthy, degraded, offline
    status: str = "active"          # active, inactive

class AIProviderRegistry:
    """
    Central repository tracking all active AI model adapters, pricing card matrices, and configurations.
    """
    def __init__(self) -> None:
        self._adapters: dict[str, IProviderAdapter] = {}
        self._specs: dict[str, ModelSpecs] = {}
        self._load_default_specs()

    def _load_default_specs(self) -> None:
        """Loads baseline specifications catalog for default active models."""
        defaults = [
            ModelSpecs(
                model_id="gemini-1.5-pro",
                provider_name="gemini",
                capabilities=["planning", "reasoning", "verification", "advisory", "translation"],
                cost_per_million_input=1.25,
                cost_per_million_output=3.75,
                context_window=1048576,
                average_latency_ms=1200.0,
                reliability_rate=0.995
            ),
            ModelSpecs(
                model_id="gpt-4o",
                provider_name="openai",
                capabilities=["planning", "reasoning", "verification", "advisory", "translation"],
                cost_per_million_input=2.50,
                cost_per_million_output=10.00,
                context_window=128000,
                average_latency_ms=1000.0,
                reliability_rate=0.99
            ),
            ModelSpecs(
                model_id="claude-3-5-sonnet-latest",
                provider_name="claude",
                capabilities=["planning", "reasoning", "verification", "advisory", "translation"],
                cost_per_million_input=3.00,
                cost_per_million_output=15.00,
                context_window=200000,
                average_latency_ms=1400.0,
                reliability_rate=0.985
            ),
            ModelSpecs(
                model_id="llama3",
                provider_name="ollama",
                capabilities=["advisory", "translation"],
                cost_per_million_input=0.0,
                cost_per_million_output=0.0,
                context_window=8192,
                average_latency_ms=400.0,
                reliability_rate=0.95
            ),
            ModelSpecs(
                model_id="groq-llama-3-70b",
                provider_name="openai",  # Leverages OpenAI compatible client routing base
                capabilities=["advisory", "translation", "planning"],
                cost_per_million_input=0.59,
                cost_per_million_output=0.79,
                context_window=8192,
                average_latency_ms=150.0,
                reliability_rate=0.97
            ),
            ModelSpecs(
                model_id="openrouter-llama-3",
                provider_name="openai",
                capabilities=["advisory", "translation"],
                cost_per_million_input=1.00,
                cost_per_million_output=2.00,
                context_window=4096,
                average_latency_ms=500.0,
                reliability_rate=0.96
            )
        ]
        for spec in defaults:
            self.register_specs(spec)

    def register_adapter(self, model_id: str, adapter: IProviderAdapter) -> None:
        """Binds a concrete executing provider adapter singleton to the registry."""
        self._adapters[model_id] = adapter
        logger.info(f"Registered model adapter for ID: {model_id}")

    def register_specs(self, specs: ModelSpecs) -> None:
        """Registers configuration specifications for a model ID."""
        self._specs[specs.model_id] = specs

    def get_adapter(self, model_id: str) -> Optional[IProviderAdapter]:
        """Resolves an executing adapter singleton by its model ID."""
        return self._adapters.get(model_id)

    def get_specs(self, model_id: str) -> Optional[ModelSpecs]:
        """Resolves metadata specifications details by its model ID."""
        return self._specs.get(model_id)

    def update_status(self, model_id: str, availability: str) -> None:
        """Hot-swaps availability status of a model (e.g. marking offline on connection drops)."""
        if model_id in self._specs:
            self._specs[model_id].availability = availability
            logger.info(f"Model ID '{model_id}' health status updated to: {availability}")

    def list_models(self) -> list[ModelSpecs]:
        """Returns lists containing all configured models specs."""
        return list(self._specs.values())
