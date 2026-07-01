import json
import logging
from typing import Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.governance.models")


class ModelMetadata(BaseModel):
    """
    Metadata specification mapping artificial intelligence models.
    """
    model_id: str = Field(..., description="Unique model identifier.")
    name: str = Field(..., description="Human-readable model name.")
    provider: str = Field(..., description="Infrastructure provider type ('Local', 'Cloud', 'Edge').")
    version: str = Field(..., description="Semantic model version.")
    capabilities: list[str] = Field(default_factory=list, description="Capabilities supported by the model.")
    latency_ms: float = Field(default=0.0, description="Average execution response latency.")
    context_window: int = Field(default=4096, description="Token size capacity of context window.")
    cost_placeholder: float = Field(default=0.0, description="Virtual pricing reference score.")
    availability: str = Field(default="high", description="Availability rating status.")
    health: str = Field(default="healthy", description="Current model health ('healthy', 'unhealthy').")
    status: str = Field(default="active", description="Governance activation state ('active', 'deprecated').")


class ModelRegistry:
    """
    Configuration-driven Model Registry tracking AI execution backends.
    """
    def __init__(self) -> None:
        self._models: dict[str, ModelMetadata] = {}

    def load_from_config(self, filepath: str) -> None:
        """
        Loads models catalog from JSON file.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("models", []):
                    model = ModelMetadata.model_validate(item)
                    self.register(model)
            logger.info(f"Model Registry loaded successfully from {filepath}.")
        except Exception as e:
            logger.error(f"Failed to load model registry configuration: {e!s}")

    def register(self, model: ModelMetadata) -> None:
        """
        Registers a model in the active registry catalog.
        """
        self._models[model.model_id] = model

    def discover(self, model_id: str) -> Optional[ModelMetadata]:
        """
        Looks up a model metadata record by ID.
        """
        return self._models.get(model_id)

    def list_models(self) -> list[ModelMetadata]:
        """
        Returns all registered model records.
        """
        return list(self._models.values())
