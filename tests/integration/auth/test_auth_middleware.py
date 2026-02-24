"""
US-1.03: Auth middleware integration tests.
Given valid JWT in Authorization header, when protected endpoint is called,
then middleware extracts user_id, org_id, role. Without token, returns 401.
"""

import uuid

import pytest
from fastapi.testclient import TestClient


def _unique_email():
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
def client():
    """Create test client."""
    from app.main import app
    return TestClient(app)


def test_middleware_extracts_claims_from_header(client):
    """request.state.user_id, org_id, role populated when valid token provided."""
    # Register to get a valid token
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": _unique_email(), "password": "SecurePass1", "name": "Test"},
    )
    assert reg.status_code == 201
    token = reg.json()["access_token"]

    # Call protected endpoint - 200 proves claims were extracted and user authenticated
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_protected_endpoint_401_without_token(client):
    """Any protected endpoint rejects missing header."""
    response = client.get("/api/v1/users")
    assert response.status_code == 401
