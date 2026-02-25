"""
US-1.04: Organization & User Management
Test Specification: invite, accept-invite, list users, role change, soft delete.
"""

import uuid

import pytest
from fastapi.testclient import TestClient


def _unique_email():
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


@pytest.fixture
def org_admin_token(client):
    """Register as org_admin and return access token."""
    email = _unique_email()
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass1", "name": "Admin"},
    )
    assert r.status_code == 201
    return r.json()["access_token"]


def test_invite_user_creates_record(client, org_admin_token):
    """User created with status=invited, org_id set."""
    r = client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"email": _unique_email(), "role": "designer", "name": "Invited User"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["email"]
    assert data["status"] == "invited"
    assert data["org_id"]
    assert data["role"] == "designer"


def test_invite_queues_email_to_service(client, org_admin_token):
    """Invitation creates user_invitations record with unique token."""
    email = _unique_email()
    r = client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"email": email, "role": "analyst", "name": "Test"},
    )
    assert r.status_code == 201
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT ui.token FROM user_invitations ui
                   JOIN users u ON u.id = ui.user_id WHERE u.email = %s""",
                (email,),
            )
            row = cur.fetchone()
    assert row, "user_invitations record should exist with token"
    assert row["token"], "Token should be non-empty"


def test_accept_invitation_sets_password(client, org_admin_token):
    """POST accept-invite sets password, status→active."""
    email = _unique_email()
    client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"email": email, "role": "designer", "name": "Accept Test"},
    )
    # Get token from DB (we need to expose it for testing - or use a test helper)
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT ui.token FROM user_invitations ui
                   JOIN users u ON u.id = ui.user_id
                   WHERE u.email = %s ORDER BY ui.created_at DESC LIMIT 1""",
                (email,),
            )
            row = cur.fetchone()
    assert row, "Invitation should exist"
    token = row["token"]
    r = client.post(
        "/api/v1/auth/accept-invite",
        json={"token": token, "password": "NewSecurePass1"},
    )
    assert r.status_code == 200
    # Verify user is active
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT status FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
    assert row["status"] == "active"


def test_accept_invitation_returns_jwt(client, org_admin_token):
    """JWT returned, contains user_id + org_id."""
    email = _unique_email()
    client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"email": email, "role": "viewer", "name": "JWT Test"},
    )
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT ui.token FROM user_invitations ui
                   JOIN users u ON u.id = ui.user_id WHERE u.email = %s
                   ORDER BY ui.created_at DESC LIMIT 1""",
                (email,),
            )
            row = cur.fetchone()
    token = row["token"]
    r = client.post(
        "/api/v1/auth/accept-invite",
        json={"token": token, "password": "SecurePass1"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # Decode JWT and check claims
    import base64
    import json
    payload_b64 = data["access_token"].split(".")[1]
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "=="))
    assert "sub" in payload  # user_id
    assert "org_id" in payload


def test_list_users_paginated(client, org_admin_token):
    """GET /users?page=1&limit=20 returns 20 max, total count."""
    r = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        params={"page": 1, "limit": 20},
    )
    assert r.status_code == 200
    data = r.json()
    assert "users" in data
    assert "total" in data
    assert isinstance(data["users"], list)
    assert len(data["users"]) <= 20


def test_change_user_role_creates_audit_log(client, org_admin_token):
    """Role updated, audit_logs entry created with before/after."""
    designer_email = _unique_email()
    client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"email": designer_email, "role": "designer", "name": "Designer"},
    )
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ui.token FROM user_invitations ui JOIN users u ON u.id = ui.user_id WHERE u.email = %s",
                (designer_email,),
            )
            row = cur.fetchone()
    client.post("/api/v1/auth/accept-invite", json={"token": row["token"], "password": "DesignerPass1"})
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (designer_email,))
            user = cur.fetchone()
    user_id = str(user["id"])
    r = client.put(
        f"/api/v1/users/{user_id}/role",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"role": "analyst"},
    )
    assert r.status_code == 200
    assert r.json()["role"] == "analyst"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT action, details_json FROM audit_logs
                   WHERE resource_type = 'user' AND resource_id = %s ORDER BY created_at DESC LIMIT 1""",
                (user_id,),
            )
            log = cur.fetchone()
    assert log
    assert log["action"] == "user_role_changed"
    assert log["details_json"]["before"] == "designer"
    assert log["details_json"]["after"] == "analyst"


def test_soft_delete_user_sets_deleted_at(client, org_admin_token):
    """DELETE sets deleted_at, user not physically removed."""
    designer_email = _unique_email()
    client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"email": designer_email, "role": "designer", "name": "To Delete"},
    )
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ui.token FROM user_invitations ui JOIN users u ON u.id = ui.user_id WHERE u.email = %s",
                (designer_email,),
            )
            row = cur.fetchone()
    client.post("/api/v1/auth/accept-invite", json={"token": row["token"], "password": "DesignerPass1"})
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (designer_email,))
            user = cur.fetchone()
    user_id = str(user["id"])
    r = client.delete(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert r.status_code == 200
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT deleted_at, status FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
    assert row["deleted_at"] is not None
    assert row["status"] == "inactive"


def test_soft_delete_invalidates_sessions(client, org_admin_token):
    """All refresh_tokens for user revoked on soft delete."""
    designer_email = _unique_email()
    client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"email": designer_email, "role": "designer", "name": "Session Test"},
    )
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ui.token FROM user_invitations ui JOIN users u ON u.id = ui.user_id WHERE u.email = %s",
                (designer_email,),
            )
            row = cur.fetchone()
    accept_r = client.post("/api/v1/auth/accept-invite", json={"token": row["token"], "password": "DesignerPass1"})
    refresh_token = accept_r.json()["refresh_token"]
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (designer_email,))
            user = cur.fetchone()
    user_id = str(user["id"])
    client.delete(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 401


def test_non_admin_403_on_user_endpoints(client):
    """Designer/Analyst/Viewer get 403 on invite, role change, delete."""
    # Register as designer (we register as org_admin by default - need to invite a designer first)
    email = _unique_email()
    admin_r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass1", "name": "Admin"},
    )
    admin_token = admin_r.json()["access_token"]
    # Invite a designer
    designer_email = _unique_email()
    client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": designer_email, "role": "designer", "name": "Designer"},
    )
    # Accept invite to get designer token
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT ui.token FROM user_invitations ui
                   JOIN users u ON u.id = ui.user_id WHERE u.email = %s
                   ORDER BY ui.created_at DESC LIMIT 1""",
                (designer_email,),
            )
            row = cur.fetchone()
    assert row
    accept_r = client.post(
        "/api/v1/auth/accept-invite",
        json={"token": row["token"], "password": "DesignerPass1"},
    )
    designer_token = accept_r.json()["access_token"]
    admin_id = None
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            admin_id = str(cur.fetchone()["id"])
    # Designer tries invite, role change, delete - all 403
    r = client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {designer_token}"},
        json={"email": _unique_email(), "role": "analyst", "name": "X"},
    )
    assert r.status_code == 403
    r = client.put(
        f"/api/v1/users/{admin_id}/role",
        headers={"Authorization": f"Bearer {designer_token}"},
        json={"role": "analyst"},
    )
    assert r.status_code == 403
    r = client.delete(
        f"/api/v1/users/{admin_id}",
        headers={"Authorization": f"Bearer {designer_token}"},
    )
    assert r.status_code == 403


def test_invitation_token_consumed_after_accept(client, org_admin_token):
    """Token cannot be replayed after successful accept."""
    email = _unique_email()
    client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"email": email, "role": "designer", "name": "Replay Test"},
    )
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT ui.token FROM user_invitations ui JOIN users u ON u.id = ui.user_id WHERE u.email = %s",
                (email,),
            )
            row = cur.fetchone()
    token = row["token"]
    r1 = client.post("/api/v1/auth/accept-invite", json={"token": token, "password": "SecurePass1"})
    assert r1.status_code == 200
    r2 = client.post("/api/v1/auth/accept-invite", json={"token": token, "password": "OtherPass1"})
    assert r2.status_code == 401


def test_expired_invitation_410(client, org_admin_token):
    """Token > 72 hours old returns 410."""
    from app.database import get_connection
    email = _unique_email()
    inv_token = str(uuid.uuid4())
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM organizations LIMIT 1")
            org = cur.fetchone()
            org_id = str(org["id"])
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users (org_id, email, name, role, status)
                   VALUES (%s, %s, %s, 'designer', 'invited')
                   RETURNING id""",
                (org_id, email, "Expired"),
            )
            user = cur.fetchone()
            user_id = str(user["id"])
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO user_invitations (user_id, token, expires_at)
                   VALUES (%s, %s, NOW() - INTERVAL '73 hours')""",
                (user_id, inv_token),
            )
    token = inv_token
    r = client.post(
        "/api/v1/auth/accept-invite",
        json={"token": token, "password": "SecurePass1"},
    )
    assert r.status_code == 410
