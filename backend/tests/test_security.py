import time

import pytest
from app.main import app
from app.security.audit_engine import AuditEngine
from app.security.auth_engine import AuthEngine
from app.security.permission_engine import PermissionEngine
from app.security.rbac_engine import RBACEngine
from app.security.session_engine import SessionEngine
from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient


def test_auth_engine() -> None:
    engine = AuthEngine(secret_key="testsecret")
    payload = {"sub": "john_doe", "role": "Farmer"}

    # 1. Sign and verify JWT access token
    token = engine.generate_jwt(payload, exp_seconds=10)
    claims = engine.decode_jwt(token)
    assert claims["sub"] == "john_doe"
    assert claims["role"] == "Farmer"

    # 2. Expiry verification
    expired_token = engine.generate_jwt(payload, exp_seconds=-5)
    with pytest.raises(ValueError, match="expired"):
        engine.decode_jwt(expired_token)

    # 3. Invalid signature check
    wrong_engine = AuthEngine(secret_key="wrongsecret")
    with pytest.raises(ValueError, match="signature"):
        wrong_engine.decode_jwt(token)

    # 4. Refresh token generation
    ref_token = engine.generate_refresh_token("john_doe")
    ref_claims = engine.decode_jwt(ref_token)
    assert ref_claims["sub"] == "john_doe"
    assert ref_claims["type"] == "refresh"

    # 5. API keys and Service tokens
    api_key = engine.generate_api_key("john_doe")
    assert api_key.startswith("km_api_")
    assert len(api_key) == 39

    svc_token = engine.generate_service_token("my_service")
    assert svc_token.startswith("km_svc_")
    assert len(svc_token) == 39

def test_rbac_engine() -> None:
    engine = RBACEngine()

    # 1. Hierarchy inheritance checks
    admin_inherited = engine.get_role_hierarchy("Admin")
    assert "Operator" in admin_inherited
    assert "Support" in admin_inherited
    assert "Farmer" in admin_inherited
    assert "Admin" in admin_inherited
    assert "Super Admin" not in admin_inherited

    # 2. is_authorized checks
    assert engine.is_authorized("Super Admin", "Admin") is True
    assert engine.is_authorized("Admin", "Super Admin") is False
    assert engine.is_authorized("Admin", "Operator") is True
    assert engine.is_authorized("Developer", "Support") is True
    assert engine.is_authorized("Farmer", "Support") is False

def test_permission_engine() -> None:
    rbac = RBACEngine()
    engine = PermissionEngine(rbac)

    # 1. Direct and inherited permission validation
    assert engine.has_permission("Admin", "admin:write") is True
    assert engine.has_permission("Operator", "page:dashboard") is True
    assert engine.has_permission("Farmer", "admin:write") is False

    # 2. Wildcard mapping checks
    assert engine.has_permission("Developer", "knowledge:schemes") is True  # Developer has knowledge:*
    assert engine.has_permission("Admin", "agent:Weather") is True       # Admin has agent:*
    assert engine.has_permission("Farmer", "agent:Weather") is True
    assert engine.has_permission("Farmer", "agent:Verifier") is False

    # 3. Component specialized checks
    assert engine.can_call_agent("Farmer", "Weather") is True
    assert engine.can_call_agent("Farmer", "Verifier") is False

    assert engine.can_access_api("Admin", "/api/v1/admin/settings") is True
    assert engine.can_access_api("Farmer", "/api/v1/admin/settings") is False
    assert engine.can_access_api("Developer", "/api/v1/observability/metrics") is True

    assert engine.can_access_knowledge("Farmer", "schemes") is True
    assert engine.can_access_knowledge("Support", "crops") is False

def test_session_engine() -> None:
    engine = SessionEngine()
    user_id = "user_1"

    # 1. Create sessions
    s1 = engine.create_session(user_id, "token_1", max_concurrent=2)
    s2 = engine.create_session(user_id, "token_2", max_concurrent=2)
    assert len(engine.get_active_sessions(user_id)) == 2

    # 2. Cap concurrent session limits (invalidate s1)
    s3 = engine.create_session(user_id, "token_3", max_concurrent=2)
    assert len(engine.get_active_sessions(user_id)) == 2
    assert engine.get_session(s1).is_active is False
    assert engine.get_session(s2).is_active is True
    assert engine.get_session(s3).is_active is True

    # 3. Touch and timeout
    assert engine.touch_session(s2) is True
    engine._sessions[s2].last_active = time.time() - 2000  # Shift back to trigger timeout
    assert engine.touch_session(s2, timeout_seconds=1800) is False
    assert engine.get_session(s2).is_active is False

    # 4. Invalidate
    engine.invalidate_session(s3)
    assert engine.get_session(s3).is_active is False

def test_audit_engine() -> None:
    engine = AuditEngine()

    # Log some events
    engine.log_audit("auth", "admin", "login", "success", {"ip": "127.0.0.1"})
    engine.log_audit("authz", "farmer_ramesh", "execute_agent:VerifierAgent", "failure", {"reason": "role"})

    events = engine.get_events(limit=10)
    assert len(events) == 2
    assert events[0].event_type == "authz"
    assert events[0].status == "failure"
    assert events[1].event_type == "auth"
    assert events[1].status == "success"

def test_rest_api_endpoints() -> None:
    with TestClient(app) as client:
        # 1. Test Login API endpoint
        login_res = client.post("/api/v1/auth/login", json={"username": "admin", "password": "password123"})
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # 2. Test Access to Protected Route (Admin Dashboard config)
        headers = {"Authorization": f"Bearer {access_token}"}
        admin_res = client.get("/api/v1/admin/config", headers=headers)
        # Config exists so it should return 200
        assert admin_res.status_code == 200

        # Unauthenticated access to admin settings should fail with 401 or 403
        unauth_res = client.get("/api/v1/admin/config", headers={"X-Test-Strict": "true"})
        assert unauth_res.status_code in (401, 403)

        # 3. Test Refresh Token endpoint
        refresh_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_res.status_code == 200
        ref_data = refresh_res.json()
        assert "access_token" in ref_data
        new_access_token = ref_data["access_token"]

        # 4. Test Audit Logs access
        audit_headers = {"Authorization": f"Bearer {new_access_token}"}
        audit_res = client.get("/api/v1/auth/audit_logs", headers=audit_headers)
        assert audit_res.status_code == 200
        assert len(audit_res.json()) >= 1

        # 5. Test Logout API endpoint
        logout_res = client.post("/api/v1/auth/logout", headers=audit_headers)
        assert logout_res.status_code == 200

        # After logout, accessing protected route with invalid token should fail
        after_logout_res = client.get("/api/v1/auth/audit_logs", headers=audit_headers)
        assert after_logout_res.status_code == 401

def test_websocket_security() -> None:
    with TestClient(app) as client:
        # Connect to websocket with invalid token should fail (disconnect with 1008)
        with pytest.raises((WebSocketDisconnect, RuntimeError)):
            with client.websocket_connect("/ws/live?token=invalid_token") as ws:
                ws.receive_json()

        # Connect to websocket without token should pass (fallback compatibility)
        with client.websocket_connect("/ws/live") as ws:
            welcome = ws.receive_json()
            assert welcome["type"] == "CONNECTED"
