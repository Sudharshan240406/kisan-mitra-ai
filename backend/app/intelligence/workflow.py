import json
import logging
import os
from typing import Any

from app.core.exceptions import OrchestratorException
from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai")

class Workflow(BaseModel):
    """
    Structured template mapping plan step nodes to active execution run steps.
    """
    workflow_id: str = Field(..., description="Unique workflow identifier.")
    name: str = Field(..., description="Human-readable name of the workflow.")
    description: str = Field(..., description="Functional details description.")
    version: str = Field(default="1.0.0", description="Semantic template version string.")
    steps: list[str] = Field(..., description="Topological execution nodes list.")
    is_active: bool = Field(default=True, description="True if this workflow can be scheduled.")

class WorkflowRegistry(BaseModel):
    """
    Central repository for registering, discovering, and validating agricultural workflows.
    """
    registry: dict[str, Workflow] = Field(default_factory=dict, description="Registry storage.")

    def register(self, workflow: Workflow) -> None:
        if not self.validate_workflow(workflow):
            raise OrchestratorException(f"Workflow '{workflow.workflow_id}' failed structural validation checks.")
        self.registry[workflow.workflow_id] = workflow
        logger.info(f"Registered workflow '{workflow.workflow_id}' (Version: {workflow.version}).")

    def remove(self, workflow_id: str) -> None:
        if workflow_id in self.registry:
            del self.registry[workflow_id]
            logger.info(f"Removed workflow '{workflow_id}' from registry.")

    def discover(self, workflow_id: str) -> Workflow:
        workflow = self.registry.get(workflow_id)
        if not workflow:
            raise OrchestratorException(f"Workflow '{workflow_id}' not found in registry catalog.")
        return workflow

    def list_workflows(self) -> list[Workflow]:
        return list(self.registry.values())

    def validate_workflow(self, workflow: Workflow) -> bool:
        # Structures checks: ID must be present and must have at least one step node
        return len(workflow.workflow_id) > 0 and len(workflow.steps) > 0

    def health(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "registered_count": len(self.registry),
            "workflow_ids": list(self.registry.keys())
        }

class WorkflowEngine:
    """
    Workflow coordination manager executing execution recipes on workflow templates.
    """
    def __init__(self) -> None:
        self.registry = WorkflowRegistry()
        self._load_config_workflows()

    def _load_config_workflows(self) -> None:
        """
        Loads workflows dynamically from config/workflows.json template.
        """
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "workflows.json"
        )

        if not os.path.exists(config_path):
            logger.warning(f"Workflow configuration file not found at '{config_path}'. Fallback loaded.")
            self._load_fallback_workflows()
            return

        try:
            with open(config_path, encoding="utf-8") as f:
                data = json.load(f)

            workflows_list = data.get("workflows", [])
            for wf_data in workflows_list:
                wf = Workflow.model_validate(wf_data)
                self.registry.register(wf)
            logger.info(f"Successfully loaded {len(workflows_list)} workflows from JSON configuration.")
        except Exception as e:
            logger.error(f"Failed to load workflows configuration from '{config_path}': {e!s}")
            self._load_fallback_workflows()

    def _load_fallback_workflows(self) -> None:
        defaults = [
            Workflow(
                workflow_id="unknown_workflow",
                name="Unknown Fallback Loop",
                description="Default loopback route.",
                steps=["Planner", "Verifier"]
            )
        ]
        for wf in defaults:
            self.registry.register(wf)

    def health_check(self) -> dict[str, Any]:
        return self.registry.health()
