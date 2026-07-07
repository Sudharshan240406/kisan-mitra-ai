import logging
from typing import Any, Dict, List, cast

from app.security.security_manager import (
    RoleRequirement,
    SecurityManager,
    get_current_user,
    get_security_manager,
)
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/auth", tags=["Enterprise Security"])
logger = logging.getLogger("kisan_mitra_ai.api.security")

class LoginRequest(BaseModel):
    username: str = Field(..., json_schema_extra={"example": "admin"})
    password: str = Field(..., json_schema_extra={"example": "password123"})

class RefreshRequest(BaseModel):
    refresh_token: str = Field(...)

@router.post("/login", response_model=Dict[str, Any])
def login(
    request_data: LoginRequest,
    security_mgr: SecurityManager = Depends(get_security_manager)
) -> Dict[str, Any]:
    """
    Authenticates username + password credentials and issues JWT Access + Refresh tokens.
    """
    result = security_mgr.authenticate_user(request_data.username, request_data.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: invalid username or password credentials."
        )
    return cast(Dict[str, Any], result)

@router.post("/logout", response_model=Dict[str, Any])
def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    security_mgr: SecurityManager = Depends(get_security_manager)
) -> Dict[str, Any]:
    """
    Terminates the user's active session.
    """
    # Invalidate by username or session ID from token if tracked
    username = current_user.get("sub", "unknown")

    # Invalidate user active sessions
    active_sessions = security_mgr.session_engine.get_active_sessions(username)
    for s in active_sessions:
        security_mgr.session_engine.invalidate_session(s.session_id)

    security_mgr.audit_engine.log_audit(
        event_type="auth",
        user_id=username,
        action="logout",
        status="success"
    )
    return {"status": "success", "message": "User session invalidated successfully."}

@router.post("/refresh", response_model=Dict[str, Any])
def refresh_token(
    refresh_data: RefreshRequest,
    security_mgr: SecurityManager = Depends(get_security_manager)
) -> Dict[str, Any]:
    """
    Generates a new access token using a valid refresh token.
    """
    try:
        claims = security_mgr.auth_engine.decode_jwt(refresh_data.refresh_token)
        if claims.get("type") != "refresh":
            raise ValueError("Token is not a refresh token")

        user_id = claims.get("sub", "unknown")
        user_info = security_mgr._mock_users.get(user_id)
        role = user_info["role"] if user_info else "Farmer"

        # Sign new access token
        access_token = security_mgr.auth_engine.generate_jwt({"sub": user_id, "role": role})
        session_id = security_mgr.session_engine.create_session(user_id, access_token)

        security_mgr.audit_engine.log_audit(
            event_type="auth",
            user_id=user_id,
            action="token_refresh",
            status="success",
            metadata={"session_id": session_id}
        )

        return {
            "access_token": access_token,
            "session_id": session_id,
            "role": role
        }
    except Exception as e:
        security_mgr.audit_engine.log_audit(
            event_type="auth",
            user_id="anonymous",
            action="token_refresh",
            status="failure",
            metadata={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Refresh token invalid: {e!s}"
        )

@router.get("/audit_logs", response_model=List[Dict[str, Any]])
def get_audit_logs(
    security_mgr: SecurityManager = Depends(get_security_manager),
    _admin_user: Dict[str, Any] = Depends(RoleRequirement("Admin"))
) -> List[Dict[str, Any]]:
    """
    Exposes security audit events to administrative roles.
    """
    events = security_mgr.audit_engine.get_events(limit=100)
    return cast(List[Dict[str, Any]], [e.model_dump() for e in events])
