import json
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.governance.prompts")


class PromptMetadata(BaseModel):
    """
    Versioned prompt template metadata supporting governance auditing.
    """
    prompt_id: str = Field(..., description="Unique prompt identifier.")
    version: str = Field(..., description="Semantic version of this prompt.")
    description: str = Field(..., description="Human-readable purpose summary.")
    owner: str = Field(default="platform", description="Owning team or service.")
    workflow: Optional[str] = Field(default=None, description="Target workflow ID if bound.")
    capability: Optional[str] = Field(default=None, description="Target capability ID if bound.")
    variables: list[str] = Field(default_factory=list, description="Template variable placeholders.")
    validation_rules: dict[str, Any] = Field(default_factory=dict, description="Constraint validation rules.")
    status: str = Field(default="active", description="Lifecycle status ('active', 'deprecated', 'draft').")
    deprecation_notes: Optional[str] = Field(default=None, description="Deprecation reason notes.")
    history: list[str] = Field(default_factory=list, description="Previous version IDs for lineage tracking.")
    ab_testing_enabled: bool = Field(default=False, description="Future A/B testing flag.")
    template: str = Field(default="", description="Prompt template text body.")


class PromptRegistry:
    """
    Configuration-driven Prompt Registry managing versioned prompt templates.
    """
    def __init__(self) -> None:
        self._prompts: dict[str, PromptMetadata] = {}
        self._versions: dict[str, list[str]] = {}  # prompt_id -> [versions]

    def load_from_config(self, filepath: str) -> None:
        """
        Loads prompts catalog from JSON configuration file.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data.get("prompts", []):
                    prompt = PromptMetadata.model_validate(item)
                    self.register(prompt)
            logger.info(f"Prompt Registry loaded {len(self._prompts)} prompts from {filepath}.")
        except Exception as e:
            logger.error(f"Failed to load prompt registry configuration: {e!s}")

    def register(self, prompt: PromptMetadata) -> None:
        """
        Registers a versioned prompt template.
        """
        key = f"{prompt.prompt_id}@{prompt.version}"
        self._prompts[key] = prompt

        if prompt.prompt_id not in self._versions:
            self._versions[prompt.prompt_id] = []
        if prompt.version not in self._versions[prompt.prompt_id]:
            self._versions[prompt.prompt_id].append(prompt.version)

        logger.info(f"Registered prompt '{prompt.prompt_id}' v{prompt.version}.")

    def discover(self, prompt_id: str, version: Optional[str] = None) -> Optional[PromptMetadata]:
        """
        Retrieves a prompt by ID. If version is None, returns the latest version.
        """
        if version:
            return self._prompts.get(f"{prompt_id}@{version}")

        versions = self._versions.get(prompt_id, [])
        if not versions:
            return None
        latest = versions[-1]
        return self._prompts.get(f"{prompt_id}@{latest}")

    def list_prompts(self) -> list[PromptMetadata]:
        """
        Returns all registered prompt metadata records.
        """
        return list(self._prompts.values())

    def get_versions(self, prompt_id: str) -> list[str]:
        """
        Returns all registered versions for a prompt ID.
        """
        return self._versions.get(prompt_id, [])

    def deprecate(self, prompt_id: str, version: str, reason: str) -> None:
        """
        Marks a specific prompt version as deprecated.
        """
        key = f"{prompt_id}@{version}"
        prompt = self._prompts.get(key)
        if not prompt:
            raise KeyError(f"Prompt '{key}' not found.")
        prompt.status = "deprecated"
        prompt.deprecation_notes = reason
        logger.info(f"Deprecated prompt '{key}': {reason}")
