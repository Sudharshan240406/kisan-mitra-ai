import contextvars
from contextlib import contextmanager
from typing import Generator, Optional

tenant_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("tenant_id", default=None)
organization_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("organization_id", default=None)
execution_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("execution_id", default=None)

def get_current_tenant_id() -> Optional[str]:
    return tenant_id_var.get()

def get_current_organization_id() -> Optional[str]:
    return organization_id_var.get()

def get_current_execution_id() -> Optional[str]:
    return execution_id_var.get()

@contextmanager
def set_tenant_context(
    tenant_id: Optional[str],
    organization_id: Optional[str] = None,
    execution_id: Optional[str] = None
) -> Generator[None, None, None]:
    """
    Asynchronous context manager to bind tenant context identifiers to the active task chain.
    """
    t_token = tenant_id_var.set(tenant_id)
    o_token = organization_id_var.set(organization_id)
    e_token = execution_id_var.set(execution_id)
    try:
        yield
    finally:
        tenant_id_var.reset(t_token)
        organization_id_var.reset(o_token)
        execution_id_var.reset(e_token)
