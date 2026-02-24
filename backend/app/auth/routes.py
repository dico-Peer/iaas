"""Auth API routes."""
import hashlib

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_connection, ensure_default_org
from app.auth.schemas import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, UserResponse
from app.auth.jwt import create_access_token, create_refresh_token, verify_token

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest):
    """Register new user with email/password."""
    with get_connection() as conn:
        org_id = ensure_default_org(conn)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM users WHERE org_id = %s AND email = %s AND deleted_at IS NULL",
                (org_id, req.email),
            )
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="Email already registered")
            password_hash = _hash_password(req.password)
            cur.execute(
                """INSERT INTO users (org_id, email, name, password_hash, role, status)
                   VALUES (%s, %s, %s, %s, 'org_admin', 'active')
                   RETURNING id, email, name, role""",
                (org_id, req.email, req.name or "", password_hash),
            )
            row = cur.fetchone()
            user_id = str(row["id"])
        access_token = create_access_token(user_id, org_id, row["role"])
        refresh_token = create_refresh_token(user_id)
        # Store refresh token hash in DB
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
                   VALUES (%s, %s, NOW() + INTERVAL '7 days')""",
                (user_id, _hash_token(refresh_token)),
            )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(id=user_id, email=row["email"], name=row["name"], role=row["role"]),
        )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Login with email/password."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, org_id, email, name, password_hash, role
                   FROM users WHERE email = %s AND deleted_at IS NULL""",
                (req.email,),
            )
            row = cur.fetchone()
        if not row or not _verify_password(req.password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user_id = str(row["id"])
        org_id = str(row["org_id"])
        access_token = create_access_token(user_id, org_id, row["role"])
        refresh_token = create_refresh_token(user_id)
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
                   VALUES (%s, %s, NOW() + INTERVAL '7 days')""",
                (user_id, _hash_token(refresh_token)),
            )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(id=user_id, email=row["email"], name=row["name"], role=row["role"]),
        )


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    """Refresh access token using refresh token."""
    payload = verify_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, org_id, email, name, role FROM users
                   WHERE id = %s AND deleted_at IS NULL""",
                (user_id,),
            )
            row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="User not found")
        org_id = str(row["org_id"])
        access_token = create_access_token(user_id, org_id, row["role"])
        return TokenResponse(access_token=access_token, refresh_token=req.refresh_token)
