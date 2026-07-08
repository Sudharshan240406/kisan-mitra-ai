import os
import shutil
from typing import Generator

import pytest
from app.core.config import settings
from app.core.container import Container
from app.main import app
from app.tenancy.organization_manager import OrganizationManager
from app.tenancy.tenant_context import (
    get_current_organization_id,
    get_current_tenant_id,
    set_tenant_context,
)
from app.tenancy.tenant_registry import TenantRegistry
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def cleanup_tenant_dirs() -> Generator[None, None, None]:
    yield
    # Clean up test tenant directories
    if os.path.exists("data/tenants"):
        shutil.rmtree("data/tenants")

def test_tenant_context_vars() -> None:
    assert get_current_tenant_id() is None

    with set_tenant_context(tenant_id="tenant_123", organization_id="org_456", execution_id="exec_789"):
        assert get_current_tenant_id() == "tenant_123"
        assert get_current_organization_id() == "org_456"

    assert get_current_tenant_id() is None

def test_tenant_registry_crud() -> None:
    registry = TenantRegistry()

    # Create
    tenant = registry.register_tenant("tenant_a", "Tenant A")
    assert tenant.id == "tenant_a"
    assert tenant.status == "active"

    # Suspend
    assert registry.suspend_tenant("tenant_a") is True
    assert registry.get_tenant("tenant_a").status == "suspended"

    # Activate
    assert registry.activate_tenant("tenant_a") is True
    assert registry.get_tenant("tenant_a").status == "active"

    # Delete
    assert registry.delete_tenant("tenant_a") is True
    assert registry.get_tenant("tenant_a") is None

def test_organization_hierarchy() -> None:
    mgr = OrganizationManager()

    # Create org, dept, team, operator
    mgr.create_organization("org_1", "Main Org", "tenant_a")
    mgr.create_department("dept_1", "Engineering", "org_1")
    mgr.create_team("team_1", "Backend Team", "dept_1")
    mgr.create_operator("op_1", "John Doe", "team_1", role="Operator")

    hierarchy = mgr.get_operator_hierarchy("op_1")
    assert hierarchy is not None
    assert hierarchy["operator"]["name"] == "John Doe"
    assert hierarchy["team"]["name"] == "Backend Team"
    assert hierarchy["department"]["name"] == "Engineering"
    assert hierarchy["organization"]["name"] == "Main Org"

def test_filesystem_isolation() -> None:
    # Ensure isolation is active via container load
    Container(settings)

    # Write to standard data file under Tenant A context
    with set_tenant_context("tenant_a"):
        with open("data/test_file.txt", "w") as f:
            f.write("tenant_a_data")

    # Write to standard data file under Tenant B context
    with set_tenant_context("tenant_b"):
        with open("data/test_file.txt", "w") as f:
            f.write("tenant_b_data")

    # Verify physical file placement isolation
    assert os.path.exists("data/tenants/tenant_a/test_file.txt") is True
    assert os.path.exists("data/tenants/tenant_b/test_file.txt") is True

    with set_tenant_context("tenant_a"):
        with open("data/test_file.txt", "r") as f:
            assert f.read() == "tenant_a_data"

    with set_tenant_context("tenant_b"):
        with open("data/test_file.txt", "r") as f:
            assert f.read() == "tenant_b_data"

def test_in_memory_personalization_isolation() -> None:
    container = Container(settings)
    platform = container.personalization_platform

    # Tenant A
    with set_tenant_context("tenant_a"):
        platform.profiles["FR-1"] = "profile_a"
        assert platform.profiles["FR-1"] == "profile_a"

    # Tenant B
    with set_tenant_context("tenant_b"):
        assert "FR-1" not in platform.profiles
        platform.profiles["FR-1"] = "profile_b"
        assert platform.profiles["FR-1"] == "profile_b"

    # Re-verify Tenant A
    with set_tenant_context("tenant_a"):
        assert platform.profiles["FR-1"] == "profile_a"

def test_rbac_hierarchical_permissions() -> None:
    container = Container(settings)
    sec_mgr = container.security_manager

    # Tenant Admin has wildcard permission
    assert sec_mgr.permission_engine.has_permission("Tenant Admin", "api:admin") is True
    assert sec_mgr.permission_engine.has_permission("Tenant Admin", "admin:write") is True

    # Organization Admin can query and read observability but not admin:write
    assert sec_mgr.permission_engine.has_permission("Organization Admin", "api:query") is True
    assert sec_mgr.permission_engine.has_permission("Organization Admin", "api:observability") is True
    assert sec_mgr.permission_engine.has_permission("Organization Admin", "admin:write") is False

    # Viewer is read-only page:dashboard/query, cannot access developer agent Planner
    assert sec_mgr.permission_engine.has_permission("Viewer", "page:dashboard") is True
    assert sec_mgr.permission_engine.has_permission("Viewer", "api:query") is True
    assert sec_mgr.permission_engine.has_permission("Viewer", "agent:Planner") is False

def test_token_claims_and_overrides() -> None:
    container = Container(settings)
    sec_mgr = container.security_manager

    # Test API Key override parsing
    claims1 = sec_mgr.verify_request_token("km_api_tenantX_orgY")
    assert claims1["tenant_id"] == "tenantX"
    assert claims1["organization_id"] == "orgY"

    # Test standard JWT claims creation and authentication
    auth_res = sec_mgr.authenticate_user("admin", "password123", tenant_id="tenantA", organization_id="orgB")
    assert auth_res is not None

    claims2 = sec_mgr.verify_request_token(auth_res["access_token"])
    assert claims2["tenant_id"] == "tenantA"
    assert claims2["organization_id"] == "orgB"

def test_e2e_tenant_query_boundary() -> None:
    with TestClient(app) as client:
        # Query 1 under Tenant A
        headers_a = {"X-Tenant-ID": "tenant_alpha"}
        payload = {
            "session_id": "sess_shared",
            "query": "Is there subsidy for wheat?",
            "background": False
        }
        res_a = client.post("/api/v1/query", json=payload, headers=headers_a)
        assert res_a.status_code == 200

        # Query 2 under Tenant B (same query content, but should be isolated)
        headers_b = {"X-Tenant-ID": "tenant_beta"}
        res_b = client.post("/api/v1/query", json=payload, headers=headers_b)
        assert res_b.status_code == 200

        # Check that caching and telemetry states are correctly registered separately
        container = client.app.state.container  # type: ignore
        with set_tenant_context("tenant_alpha"):
            assert len(container.performance_manager.latencies) == 1
        with set_tenant_context("tenant_beta"):
            assert len(container.performance_manager.latencies) == 1
