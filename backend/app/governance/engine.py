import logging
import time
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.governance.engine")


class VersionRecord(BaseModel):
    """
    Version tracking record for governed platform artifacts.
    """
    artifact_type: str = Field(..., description="Type of artifact ('plugin', 'model', 'prompt', 'workflow', 'capability', 'ontology', 'policy').")
    artifact_id: str = Field(..., description="Artifact unique identifier.")
    version: str = Field(..., description="Active semantic version.")
    previous_version: Optional[str] = Field(default=None, description="Prior version before upgrade.")
    status: str = Field(default="active", description="Governance status ('active', 'deprecated', 'draft').")
    timestamp: float = Field(default_factory=time.time, description="Registration epoch timestamp.")


class GovernanceReport(BaseModel):
    """
    Aggregate governance audit report structure.
    """
    total_artifacts: int = 0
    active_count: int = 0
    deprecated_count: int = 0
    draft_count: int = 0
    artifact_breakdown: dict[str, int] = Field(default_factory=dict)
    version_records: list[VersionRecord] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class GovernanceEngine:
    """
    Centralized Governance Engine auditing version control across all platform artifacts.
    Manages lifecycle governance for plugins, models, prompts, workflows,
    capabilities, ontologies, policies, decision strategies, and conversation strategies.
    """
    def __init__(self) -> None:
        self._records: dict[str, VersionRecord] = {}

    def register_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        version: str,
        previous_version: Optional[str] = None,
        status: str = "active"
    ) -> VersionRecord:
        """
        Registers a new versioned artifact into the governance ledger.
        """
        key = f"{artifact_type}:{artifact_id}"
        existing = self._records.get(key)

        record = VersionRecord(
            artifact_type=artifact_type,
            artifact_id=artifact_id,
            version=version,
            previous_version=existing.version if existing else previous_version,
            status=status
        )
        self._records[key] = record
        logger.info(f"Governance: registered {artifact_type} '{artifact_id}' v{version}.")
        return record

    def deprecate_artifact(self, artifact_type: str, artifact_id: str, reason: str = "") -> None:
        """
        Marks an artifact as deprecated in the governance ledger.
        """
        key = f"{artifact_type}:{artifact_id}"
        record = self._records.get(key)
        if not record:
            raise KeyError(f"Governance artifact '{key}' not found.")
        record.status = "deprecated"
        logger.info(f"Governance: deprecated {artifact_type} '{artifact_id}': {reason}")

    def get_artifact(self, artifact_type: str, artifact_id: str) -> Optional[VersionRecord]:
        """
        Retrieves a governed artifact record.
        """
        return self._records.get(f"{artifact_type}:{artifact_id}")

    def list_by_type(self, artifact_type: str) -> list[VersionRecord]:
        """
        Lists all governed artifacts matching a type filter.
        """
        return [r for r in self._records.values() if r.artifact_type == artifact_type]

    def generate_report(self) -> GovernanceReport:
        """
        Generates a comprehensive governance audit report.
        """
        all_records = list(self._records.values())
        active = [r for r in all_records if r.status == "active"]
        deprecated = [r for r in all_records if r.status == "deprecated"]
        draft = [r for r in all_records if r.status == "draft"]

        breakdown: dict[str, int] = {}
        for r in all_records:
            breakdown[r.artifact_type] = breakdown.get(r.artifact_type, 0) + 1

        issues: list[str] = []
        # Detect version duplicates (same type+id registered twice is handled by overwrite)
        # Detect deprecated artifacts still marked as dependencies (future enhancement)

        return GovernanceReport(
            total_artifacts=len(all_records),
            active_count=len(active),
            deprecated_count=len(deprecated),
            draft_count=len(draft),
            artifact_breakdown=breakdown,
            version_records=all_records,
            issues=issues
        )

    def auto_register_from_registries(
        self,
        plugins: Any = None,
        models: Any = None,
        prompts: Any = None,
        workflows: Any = None,
        capabilities: Any = None
    ) -> None:
        """
        Bulk-registers artifacts from existing platform registries into governance.
        """
        if plugins is not None:
            for plugin in plugins.list_plugins():
                meta = plugin.metadata
                self.register_artifact("plugin", meta.plugin_id, meta.version, status=meta.status)

        if models is not None:
            for model in models.list_models():
                self.register_artifact("model", model.model_id, model.version, status=model.status)

        if prompts is not None:
            for prompt in prompts.list_prompts():
                self.register_artifact("prompt", prompt.prompt_id, prompt.version, status=prompt.status)

        if workflows is not None:
            for wf_def in workflows:
                wf_id = wf_def.get("workflow_id", "unknown")
                wf_ver = wf_def.get("version", "0.0.0")
                self.register_artifact("workflow", wf_id, wf_ver)

        if capabilities is not None:
            for cap in capabilities:
                cap_id = cap.get("capability_id", "unknown")
                cap_ver = cap.get("version", "0.0.0")
                self.register_artifact("capability", cap_id, cap_ver)
