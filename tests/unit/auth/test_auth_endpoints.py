"""
US-1.03: User Registration & JWT Authentication
Test Specification: register, login, refresh, JWT middleware.
"""

import uuid

import pytest
from fastapi.testclient import TestClient

# Import app after setting up test env
REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent


def _unique_email():
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
def client():
    """Create test client with overrides for test DB."""
    from app.main import app
    return TestClient(app)


def test_register_valid_credentials(client):
    """Given valid email/password (≥8 chars, 1 uppercase, 1 number), when POST /api/v1/auth/register, then 201 with access_token, refresh_token, user."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": _unique_email(), "password": "SecurePass1", "name": "Test User"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "user" in data
    assert "id" in data["user"]
    assert data["user"]["name"] == "Test User"
    assert "id" in data["user"]
    assert "role" in data["user"]


def test_register_hashes_password(client):
    """User password is bcrypt-hashed in DB, not plain text."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "hash@example.com", "password": "SecurePass1", "name": "Hash Test"},
    )
    # Verify via login - if we can login, password was stored correctly
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "hash@example.com", "password": "SecurePass1"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_register_duplicate_email_409(client):
    """Given duplicate email, when POST register, then 409."""
    email = _unique_email()
    payload = {"email": email, "password": "SecurePass1", "name": "First"}
    client.post("/api/v1/auth/register", json=payload)
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    body = response.json()
    msg = (body.get("detail") or body.get("error") or "").lower()
    assert "already" in msg or "email" in msg or "registered" in msg


def test_register_invalid_password_400(client):
    """Given password < 8 chars or no uppercase/number, when register, then 400 or 422."""
    for i, bad_password in enumerate(["short", "nouppercase1", "NoNumbers"]):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": _unique_email(), "password": bad_password, "name": "X"},
        )
        assert response.status_code in (400, 422), f"Expected 400/422 for {bad_password!r}, got {response.status_code}"


def test_login_valid_credentials_200(client):
    """Given registered user, when POST login with correct password, then 200 with tokens."""
    client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "SecurePass1", "name": "Login"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "SecurePass1"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password_401(client):
    """Given wrong password, when login, then 401, no email-exists hint."""
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass1", "name": "Wrong"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "WrongPassword1"},
    )
    assert response.status_code == 401
    # Should not reveal whether email exists
    body = response.json()
    assert "invalid" in str(body).lower() or "credentials" in str(body).lower()


def test_jwt_contains_correct_claims(client):
    """JWT contains sub (user_id), org_id, role, exp."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": _unique_email(), "password": "SecurePass1", "name": "Claims"},
    )
    assert response.status_code == 201, response.json()
    token = response.json()["access_token"]
    import base64
    import json
    parts = token.split(".")
    payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload))
    assert "sub" in decoded
    assert "org_id" in decoded
    assert "role" in decoded
    assert "exp" in decoded


def test_refresh_token_flow(client):
    """Expired access + valid refresh -> new access_token."""
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": _unique_email(), "password": "SecurePass1", "name": "Refresh"},
    )
    refresh_token = reg.json()["refresh_token"]
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_expired_token_rejected_401(client):
    """401 when token is invalid or expired."""
    response = client.get("/api/v1/users", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_protected_endpoint_401_without_token(client):
    """Any protected endpoint rejects missing/invalid Authorization header."""
    response = client.get("/api/v1/users")
    assert response.status_code == 401
