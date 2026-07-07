from typing import Any, Dict, Set

# Mappings of Role to direct scopes and capabilities
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    "Super Admin": {"*"},
    "Admin": {
        "page:dashboard", "page:analytics", "page:farmer", "page:admin",
        "api:query", "api:observability", "api:admin", "api:telemetry",
        "agent:*",
        "knowledge:*",
        "admin:read", "admin:write"
    },
    "Operator": {
        "page:dashboard", "page:farmer",
        "api:query", "api:observability", "api:telemetry",
        "agent:Weather", "agent:Market", "agent:Knowledge", "agent:GovernmentScheme",
        "knowledge:weather", "knowledge:market", "knowledge:schemes", "knowledge:crops"
    },
    "Support": {
        "page:farmer",
        "api:query",
        "agent:Weather", "agent:Market",
        "knowledge:weather", "knowledge:market"
    },
    "Farmer": {
        "page:farmer",
        "api:query",
        "agent:Weather", "agent:Market", "agent:GovernmentScheme",
        "knowledge:weather", "knowledge:market", "knowledge:schemes"
    },
    "Developer": {
        "page:analytics",
        "api:observability", "api:telemetry",
        "agent:Verifier", "agent:Planner",
        "knowledge:*"
    }
}

class PermissionEngine:
    """
    Granular permission verification engine supporting:
    - Page permissions (e.g. 'page:dashboard')
    - API permissions (e.g. 'api:admin')
    - Agent permissions (e.g. 'agent:WeatherAgent')
    - Knowledge permissions (e.g. 'knowledge:schemes')
    - Admin permissions (e.g. 'admin:write')
    """
    def __init__(self, rbac_engine: Any = None) -> None:
        # We can accept an rbac_engine to support inheritance if needed
        self.rbac_engine = rbac_engine

    def has_permission(self, role: str, permission: str) -> bool:
        """
        Validates if user role has a specific permission scope.
        Supports wildcard checks '*' and role inheritance expansion.
        """
        roles_to_check = {role}
        if self.rbac_engine:
            roles_to_check = self.rbac_engine.get_role_hierarchy(role)

        for r in roles_to_check:
            perms = ROLE_PERMISSIONS.get(r, set())
            if "*" in perms:
                return True
            if permission in perms:
                return True

            # Sub-category wildcards (e.g. agent:* matched by agent:WeatherAgent)
            if ":" in permission:
                prefix = permission.split(":", maxsplit=1)[0]
                if f"{prefix}:*" in perms:
                    return True

        return False

    def can_call_agent(self, role: str, agent_name: str) -> bool:
        """
        Verifies if role can execute the specified Specialist Agent.
        """
        # Strip suffixes or normalise names
        return self.has_permission(role, f"agent:{agent_name}")

    def can_access_api(self, role: str, api_path: str) -> bool:
        """
        Verifies if role can request the specified API prefix/path.
        """
        # Map path prefixes to API permission parameters
        if api_path.startswith("/api/v1/admin") or api_path.startswith("/admin"):
            return self.has_permission(role, "api:admin")
        if api_path.startswith("/api/v1/observability"):
            return self.has_permission(role, "api:observability")
        if api_path.startswith("/api/v1/telemetry"):
            return self.has_permission(role, "api:telemetry")
        if api_path.startswith("/api/v1/query") or api_path.startswith("/api/v1/ai"):
            return self.has_permission(role, "api:query")
        return True  # Public routes by default

    def can_access_knowledge(self, role: str, module_name: str) -> bool:
        """
        Verifies if role has permission to read the specified knowledge base modules.
        """
        return self.has_permission(role, f"knowledge:{module_name}")
