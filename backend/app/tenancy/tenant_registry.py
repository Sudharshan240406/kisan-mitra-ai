import time
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Tenant(BaseModel):
    id: str
    name: str
    status: str = "active"  # active | suspended | inactive
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TenantRegistry:
    """
    Registry management class controlling tenant details, activations, and suspensions.
    """
    def __init__(self) -> None:
        self._tenants: Dict[str, Tenant] = {}

    def register_tenant(self, tenant_id: str, name: str, metadata: Optional[Dict[str, Any]] = None) -> Tenant:
        tenant = Tenant(id=tenant_id, name=name, metadata=metadata or {})
        self._tenants[tenant_id] = tenant
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def suspend_tenant(self, tenant_id: str) -> bool:
        tenant = self.get_tenant(tenant_id)
        if tenant:
            tenant.status = "suspended"
            return True
        return False

    def activate_tenant(self, tenant_id: str) -> bool:
        tenant = self.get_tenant(tenant_id)
        if tenant:
            tenant.status = "active"
            return True
        return False

    def delete_tenant(self, tenant_id: str) -> bool:
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]
            return True
        return False

    def list_tenants(self) -> Dict[str, Tenant]:
        return self._tenants
