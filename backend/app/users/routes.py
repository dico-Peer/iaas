"""Users API routes - protected by JWT."""
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def list_users(current_user: dict = Depends(get_current_user)):
    """List users in organization. Requires authentication."""
    return {"users": [], "total": 0}  # Placeholder; full impl in US-1.04
