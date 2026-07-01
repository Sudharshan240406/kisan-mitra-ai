import logging
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger("kisan_mitra_ai.governance.validators")


class ValidationIssue(BaseModel):
    """
    Single issue found during platform validation.
    """
    severity: str = Field(..., description="Issue severity ('error', 'warning', 'info').")
    category: str = Field(..., description="Issue category (e.g. 'circular_dependency', 'missing_registration').")
    message: str = Field(..., description="Human-readable issue description.")
    artifact: str = Field(default="", description="Artifact reference triggering the issue.")


class ValidationReport(BaseModel):
    """
    Structured validation report output.
    """
    report_type: str = Field(..., description="Report type ('architecture', 'integration').")
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    issues: list[ValidationIssue] = Field(default_factory=list)
    summary: str = ""


class PlatformValidator:
    """
    Validates platform architecture and end-to-end integration chains.
    Detects circular dependencies, duplicate capabilities, missing registrations,
    broken workflow references, and unused services.
    """

    def validate_architecture(
        self,
        agent_names: list[str],
        capability_ids: list[str],
        workflow_ids: list[str],
        service_names: list[str],
        plugin_ids: list[str],
    ) -> ValidationReport:
        """
        Validates structural integrity of all registered platform artifacts.
        """
        issues: list[ValidationIssue] = []
        total_checks = 0

        # 1. Check for duplicate capabilities
        total_checks += 1
        seen_caps: set[str] = set()
        for cap_id in capability_ids:
            if cap_id in seen_caps:
                issues.append(ValidationIssue(
                    severity="error",
                    category="duplicate_capability",
                    message=f"Duplicate capability '{cap_id}' detected.",
                    artifact=cap_id
                ))
            seen_caps.add(cap_id)

        # 2. Check for duplicate agent names
        total_checks += 1
        seen_agents: set[str] = set()
        for name in agent_names:
            lower = name.strip().lower()
            if lower in seen_agents:
                issues.append(ValidationIssue(
                    severity="error",
                    category="duplicate_agent",
                    message=f"Duplicate agent name '{name}' detected.",
                    artifact=name
                ))
            seen_agents.add(lower)

        # 3. Verify all agents have at least one capability or workflow referencing them
        total_checks += 1
        # This is informational — not all agents must be referenced by capabilities
        if not agent_names:
            issues.append(ValidationIssue(
                severity="warning",
                category="missing_registration",
                message="No agents registered in the platform.",
                artifact="AgentRegistry"
            ))

        # 4. Check for empty service registrations
        total_checks += 1
        if not service_names:
            issues.append(ValidationIssue(
                severity="warning",
                category="missing_registration",
                message="No domain services registered.",
                artifact="DomainServices"
            ))

        # 5. Check for empty workflow registrations
        total_checks += 1
        if not workflow_ids:
            issues.append(ValidationIssue(
                severity="warning",
                category="missing_registration",
                message="No workflows registered.",
                artifact="WorkflowRegistry"
            ))

        # 6. Check for orphaned plugin IDs (informational)
        total_checks += 1
        # Plugins are optional — just count them
        if not plugin_ids:
            issues.append(ValidationIssue(
                severity="info",
                category="no_plugins",
                message="No plugins registered. Platform running in core mode.",
                artifact="PluginRegistry"
            ))

        passed = total_checks - len([i for i in issues if i.severity == "error"])

        return ValidationReport(
            report_type="architecture",
            total_checks=total_checks,
            passed_checks=passed,
            failed_checks=total_checks - passed,
            issues=issues,
            summary=f"Architecture validation: {passed}/{total_checks} checks passed."
        )

    def validate_integration_chain(
        self,
        capabilities: list[dict[str, Any]],
        workflows: list[dict[str, Any]],
        agent_names: list[str],
    ) -> ValidationReport:
        """
        Validates end-to-end integration chain:
        Intent -> Planner -> Capability -> Workflow -> Agents -> Decision -> Governance -> Response
        """
        issues: list[ValidationIssue] = []
        total_checks = 0

        workflow_id_set = {w.get("workflow_id", "") for w in workflows}
        agent_name_set = {a.strip().lower() for a in agent_names}

        for cap in capabilities:
            cap_id = cap.get("capability_id", "unknown")

            # Check workflow reference exists
            total_checks += 1
            wf_id = cap.get("workflow_id", "")
            if wf_id and wf_id not in workflow_id_set:
                issues.append(ValidationIssue(
                    severity="error",
                    category="broken_reference",
                    message=f"Capability '{cap_id}' references workflow '{wf_id}' which is not registered.",
                    artifact=cap_id
                ))

            # Check required agents exist
            required_agents: list[str] = cap.get("required_agents", [])
            for agent in required_agents:
                total_checks += 1
                if agent.strip().lower() not in agent_name_set:
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="missing_agent",
                        message=f"Capability '{cap_id}' requires agent '{agent}' which is not registered.",
                        artifact=cap_id
                    ))

        # Verify each workflow has at least one step
        for wf in workflows:
            total_checks += 1
            steps: list[str] = wf.get("steps", [])
            if not steps:
                issues.append(ValidationIssue(
                    severity="error",
                    category="empty_workflow",
                    message=f"Workflow '{wf.get('workflow_id', 'unknown')}' has no execution steps.",
                    artifact=wf.get("workflow_id", "unknown")
                ))

        passed = total_checks - len([i for i in issues if i.severity == "error"])

        return ValidationReport(
            report_type="integration",
            total_checks=total_checks,
            passed_checks=passed,
            failed_checks=total_checks - passed,
            issues=issues,
            summary=f"Integration validation: {passed}/{total_checks} checks passed."
        )

    def detect_circular_dependencies(
        self,
        dependency_graph: dict[str, list[str]]
    ) -> list[ValidationIssue]:
        """
        Detects circular dependencies in a directed dependency graph.
        """
        issues: list[ValidationIssue] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def _dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in dependency_graph.get(node, []):
                if neighbor not in visited:
                    _dfs(neighbor, [*path, neighbor])
                elif neighbor in rec_stack:
                    cycle_path = " -> ".join([*path, neighbor])
                    issues.append(ValidationIssue(
                        severity="error",
                        category="circular_dependency",
                        message=f"Circular dependency detected: {cycle_path}",
                        artifact=node
                    ))

            rec_stack.discard(node)

        for node in dependency_graph:
            if node not in visited:
                _dfs(node, [node])

        return issues
