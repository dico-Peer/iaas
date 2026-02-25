"""
US-2.01: Project org isolation.
User only sees projects from their own organization.
"""

import uuid

import pytest
import requests


def _unique_email():
    return f"test-{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture(scope="module")
def api_base():
    return "http://localhost:8000"


def test_user_only_sees_own_org_projects(api_base):
    """Org isolation enforced - user A cannot see user B's org projects."""
    # Register user A (creates org A)
    email_a = _unique_email()
    r_a = requests.post(
        f"{api_base}/api/v1/auth/register",
        json={"email": email_a, "password": "SecurePass1", "name": "User A"},
    )
    assert r_a.status_code == 201
    token_a = r_a.json()["access_token"]

    # User A creates project
    r_create = requests.post(
        f"{api_base}/api/v1/projects",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"title": "Org A Project"},
    )
    assert r_create.status_code == 201
    project_id = r_create.json()["id"]

    # Register user B (creates org B - different org)
    email_b = _unique_email()
    r_b = requests.post(
        f"{api_base}/api/v1/auth/register",
        json={"email": email_b, "password": "SecurePass1", "name": "User B"},
    )
    assert r_b.status_code == 201
    token_b = r_b.json()["access_token"]

    # User B cannot see User A's project
    r_list = requests.get(
        f"{api_base}/api/v1/projects",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r_list.status_code == 200
    projects = r_list.json()["projects"]
    ids = [p["id"] for p in projects]
    assert project_id not in ids

    # User B cannot get project by ID
    r_get = requests.get(
        f"{api_base}/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r_get.status_code == 404
