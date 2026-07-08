from typing import Dict, List, Set


class RBACEngine:
    """
    Role-Based Access Control Engine managing role permissions inheritance and classification:
    Roles:
    - Super Admin
    - Admin
    - Operator
    - Support
    - Farmer
    - Developer
    """
    def __init__(self) -> None:
        # Define hierarchical structure where keys inherit values
        self._hierarchy: Dict[str, List[str]] = {
            "Super Admin": ["Tenant Admin", "Admin", "Operator", "Support", "Farmer", "Developer"],
            "Tenant Admin": ["Organization Admin", "Admin", "Operator", "Support", "Farmer", "Viewer"],
            "Organization Admin": ["Operator", "Support", "Farmer", "Viewer"],
            "Admin": ["Operator", "Support", "Farmer"],
            "Operator": ["Support", "Farmer", "Viewer"],
            "Support": ["Farmer", "Viewer"],
            "Developer": ["Support"],
            "Farmer": ["Viewer"],
            "Viewer": []
        }

    def get_role_hierarchy(self, role: str) -> Set[str]:
        """
        Recursively resolves all roles inherited by a given role.
        """
        inherited: Set[str] = {role}
        queue = list(self._hierarchy.get(role, []))

        while queue:
            current = queue.pop(0)
            if current not in inherited:
                inherited.add(current)
                # Expand inherited roles
                queue.extend(self._hierarchy.get(current, []))

        return inherited

    def is_authorized(self, user_role: str, target_role: str) -> bool:
        """
        Returns True if user_role has access rights corresponding to target_role.
        """
        # If user_role is Developer, it has its own distinct access, but inherits Farmer/Support
        # Admin inherits Operator/Support/Farmer
        # Super Admin inherits everything
        inherited = self.get_role_hierarchy(user_role)
        return target_role in inherited
