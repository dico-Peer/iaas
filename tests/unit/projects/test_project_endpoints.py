"""
US-2.01: Interview Project CRUD
Test Specification: create, list, update, delete, clone.
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
    """Register as org_admin and return access token. (register always creates org_admin.)"""
    email = _unique_email()
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass1", "name": "Admin"},
    )
    assert r.status_code == 201
    return r.json()["access_token"]


def test_create_project_returns_201(client, org_admin_token):
    """Project created, status=draft, has id."""
    r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={
            "title": "AI Research",
            "description": "Study AI adoption",
            "research_objectives": "Understand barriers",
            "target_audience": "Developers",
            "language": "en",
            "modality": "text",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["id"]
    assert data["title"] == "AI Research"
    assert data["status"] == "draft"
    assert data["description"] == "Study AI adoption"
    assert data["research_objectives"] == "Understand barriers"
    assert data["target_audience"] == "Developers"
    assert data["language"] == "en"
    assert data["modality"] == "text"


def test_create_project_sets_defaults(client, org_admin_token):
    """language defaults to EN, modality=text if not specified."""
    r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "Minimal Project"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["language"] == "en"
    assert data["modality"] == "text"
    assert data["status"] == "draft"


def test_list_projects_sorted_by_modified(client, org_admin_token):
    """Projects ordered DESC by updated_at."""
    for i in range(3):
        client.post(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={"title": f"Project {i}"},
        )
    r = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert r.status_code == 200
    projects = r.json()["projects"]
    assert len(projects) >= 3
    # Most recently modified first
    for i in range(len(projects) - 1):
        assert projects[i]["updated_at"] >= projects[i + 1]["updated_at"]


def test_update_project_partial(client, org_admin_token):
    """PATCH updates only provided fields."""
    create_r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "Original", "description": "Keep me"},
    )
    assert create_r.status_code == 201
    pid = create_r.json()["id"]
    r = client.put(
        f"/api/v1/projects/{pid}",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "Updated Title"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Keep me"


def test_update_creates_audit_log(client, org_admin_token):
    """Audit entry created with before/after JSON."""
    create_r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "Audit Test"},
    )
    pid = create_r.json()["id"]
    client.put(
        f"/api/v1/projects/{pid}",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "Audit Updated"},
    )
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT action, details_json FROM audit_logs
                   WHERE resource_type = 'project' AND resource_id = %s
                   ORDER BY created_at DESC LIMIT 1""",
                (pid,),
            )
            row = cur.fetchone()
    assert row
    assert row["action"] == "project_updated"
    import json
    details = json.loads(row["details_json"])
    assert "before" in details
    assert "after" in details
    assert details["after"].get("title") == "Audit Updated"


def test_delete_draft_project_204(client, org_admin_token):
    """DELETE draft project returns 204, soft-deleted."""
    create_r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "To Delete", "status": "draft"},
    )
    pid = create_r.json()["id"]
    r = client.delete(
        f"/api/v1/projects/{pid}",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert r.status_code == 204
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT deleted_at FROM interview_projects WHERE id = %s",
                (pid,),
            )
            row = cur.fetchone()
    assert row and row["deleted_at"] is not None


def test_prevent_delete_active_409(client, org_admin_token):
    """DELETE active project returns 409."""
    create_r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "Active Project"},
    )
    pid = create_r.json()["id"]
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE interview_projects SET status = 'active' WHERE id = %s",
                (pid,),
            )
    r = client.delete(
        f"/api/v1/projects/{pid}",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert r.status_code == 409
    assert "Active projects cannot be deleted" in r.json().get("detail", "")


def test_analyst_gets_403_on_create_project(client, org_admin_token):
    """Analyst and viewer receive 403 on POST /api/v1/projects."""
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass1", "name": "Admin"},
    )
    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePass1"},
    )
    admin_token = r_login.json()["access_token"]
    invite_email = _unique_email()
    client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"email": invite_email, "role": "analyst", "name": "Analyst"},
    )
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT token FROM user_invitations ui JOIN users u ON u.id = ui.user_id WHERE u.email = %s",
                (invite_email,),
            )
            row = cur.fetchone()
    token = row["token"]
    client.post(
        "/api/v1/auth/accept-invite",
        json={"token": token, "password": "SecurePass1", "name": "Analyst"},
    )
    r_login_analyst = client.post(
        "/api/v1/auth/login",
        json={"email": invite_email, "password": "SecurePass1"},
    )
    analyst_token = r_login_analyst.json()["access_token"]
    r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"title": "Forbidden"},
    )
    assert r.status_code == 403


def test_clone_project_deep_copy(client, org_admin_token):
    """Questions + agents duplicated, new title '[Original] — Copy'."""
    create_r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "Original"},
    )
    pid = create_r.json()["id"]
    from app.database import get_connection
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO interview_questions (project_id, order_index, question_text, question_type)
                   VALUES (%s, 0, 'Q1?', 'open')""",
                (pid,),
            )
            cur.execute(
                """INSERT INTO agents (project_id, name, system_prompt)
                   VALUES (%s, 'Agent1', 'You are helpful')""",
                (pid,),
            )
    r = client.post(
        f"/api/v1/projects/{pid}/clone",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["id"] != pid
    assert data["title"] == "[Original] — Copy"
    assert data["status"] == "draft"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as c FROM interview_questions WHERE project_id = %s",
                (data["id"],),
            )
            q_count = cur.fetchone()["c"]
            cur.execute(
                "SELECT COUNT(*) as c FROM agents WHERE project_id = %s",
                (data["id"],),
            )
            a_count = cur.fetchone()["c"]
    assert q_count == 1
    assert a_count == 1
