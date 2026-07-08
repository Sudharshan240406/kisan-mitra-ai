import contextvars
from typing import Any, Optional

tenant_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)
organization_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("organization_id", default=None)
execution_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("execution_id", default=None)

def get_current_tenant_id() -> Optional[str]:
    return tenant_id_var.get()

def get_current_organization_id() -> Optional[str]:
    return organization_id_var.get()

def get_current_execution_id() -> Optional[str]:
    return execution_id_var.get()

class set_tenant_context:
    """
    Asynchronous context manager to bind tenant context identifiers to the active task chain.
    """
    def __init__(
        self,
        tenant_id: Optional[str],
        organization_id: Optional[str] = None,
        execution_id: Optional[str] = None
    ) -> None:
        self.tenant_id = tenant_id
        self.organization_id = organization_id
        self.execution_id = execution_id
        self.t_token = None
        self.o_token = None
        self.e_token = None

    def __enter__(self) -> "set_tenant_context":
        self.t_token = tenant_id_var.set(self.tenant_id)
        self.o_token = organization_id_var.set(self.organization_id)
        self.e_token = execution_id_var.set(self.execution_id)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.t_token:
            tenant_id_var.reset(self.t_token)
        if self.o_token:
            organization_id_var.reset(self.o_token)
        if self.e_token:
            execution_id_var.reset(self.e_token)
