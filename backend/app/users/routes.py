"""Users API routes - protected by JWT."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth.dependencies import get_current_user, get_current_org_admin
from app.database import get_connection
from app.users.schemas import InviteRequest

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_ROLES = ("designer", "analyst", "viewer")


@router.get("")
def list_users(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """List users in organization. Paginated. Requires authentication."""
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    offset = (page - 1) * limit
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, name, email, role, status, last_login, created_at
                   FROM users
                   WHERE org_id = %s AND deleted_at IS NULL
                   ORDER BY created_at DESC
                   LIMIT %s OFFSET %s""",
                (org_id, limit, offset),
            )
            rows = cur.fetchall()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as total FROM users WHERE org_id = %s AND deleted_at IS NULL",
                (org_id,),
            )
            total = cur.fetchone()["total"]
    users = [
        {
            "id": str(r["id"]),
            "name": r["name"],
            "email": r["email"],
            "role": r["role"],
            "status": r["status"],
            "last_login": r["last_login"].isoformat() if r["last_login"] else None,
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]
    return {"users": users, "total": total}


@router.post("/invite", status_code=201)
def invite_user(
    req: InviteRequest,
    current_user: dict = Depends(get_current_org_admin),
):
    """Invite user to organization. Org admin only."""
    if req.role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail=f"Role must be one of {ALLOWED_ROLES}")
    org_id = current_user.get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    token = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE org_id = %s AND email = %s AND deleted_at IS NULL",
                (org_id, req.email),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="User already exists in organization")
            cur.execute(
                """INSERT INTO users (org_id, email, name, role, status)
                   VALUES (%s, %s, %s, %s, 'invited')
                   RETURNING id, email, name, role, status""",
                (org_id, req.email, req.name or "", req.role),
            )
            row = cur.fetchone()
            user_id = str(row["id"])
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO user_invitations (user_id, token, expires_at)
                   VALUES (%s, %s, NOW() + INTERVAL '72 hours')""",
                (user_id, token),
            )
    return {
        "id": user_id,
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "status": row["status"],
        "org_id": org_id,
    }
