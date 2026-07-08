import logging
from typing import Any, Dict, Optional

from .organization_manager import OrganizationManager
from .tenant_registry import Tenant, TenantRegistry

logger = logging.getLogger("kisan_mitra_ai.tenancy.manager")

class TenantManager:
    """
    Unified manager orchestrating tenant lifecycle routines and workspace directories.
    """
    def __init__(self, container: Any = None) -> None:
        self.container = container
        self.registry = TenantRegistry()
        self.org_manager = OrganizationManager()

    def create_tenant_workspace(self, tenant_id: str, name: str, metadata: Optional[Dict[str, Any]] = None) -> Tenant:
        """
        Creates a new tenant and sets up local directory partitions if required.
        """
        tenant = self.registry.register_tenant(tenant_id, name, metadata)
        logger.info(f"[TenantManager] Provisioned workspace context for tenant '{tenant_id}' name '{name}'")
        return tenant
