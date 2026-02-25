"""Auth dependencies for FastAPI."""
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt import verify_token

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    """Extract and validate JWT from Authorization header. Returns user claims."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = verify_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Authentication required")
    return payload


def get_current_org_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Require org_admin or system_admin role. Returns 403 for others."""
    role = current_user.get("role", "")
    if role not in ("org_admin", "system_admin"):
        raise HTTPException(status_code=403, detail="Forbidden: org admin required")
    return current_user
