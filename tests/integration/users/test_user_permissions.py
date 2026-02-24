"""
US-1.04: Org isolation in user list.
Org A admin only sees Org A users.
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


def test_org_isolation_in_user_list(client):
    """Org A admin only sees Org A users."""
    from app.database import get_connection
    # Register admin A (org A = default org)
    email_a = _unique_email()
    r_a = client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "SecurePass1", "name": "Admin A"},
    )
    assert r_a.status_code == 201
    token_a = r_a.json()["access_token"]
    # Get org A id from JWT or DB
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT org_id FROM users WHERE email = %s", (email_a,))
            org_a_id = str(cur.fetchone()["org_id"])
    # Create org B and add a user in org B (not visible to org A admin)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO organizations (name, slug, settings_json)
                   VALUES ('Org B', 'org-b', '{}') RETURNING id""",
            )
            org_b_id = str(cur.fetchone()["id"])
            cur.execute(
                """INSERT INTO users (org_id, email, name, role, status)
                   VALUES (%s, %s, 'User B', 'designer', 'active')""",
                (org_b_id, _unique_email()),
            )
    # List users as admin A - should NOT see org B user
    r = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {token_a}"},
        params={"page": 1, "limit": 20},
    )
    assert r.status_code == 200
    users = r.json()["users"]
    # All returned users must be in org A
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT email FROM users WHERE org_id = %s AND deleted_at IS NULL", (org_b_id,))
            org_b_emails = {row["email"] for row in cur.fetchall()}
    for u in users:
        assert u["email"] not in org_b_emails, "Org A admin must not see Org B users"
