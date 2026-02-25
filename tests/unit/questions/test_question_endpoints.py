"""
US-2.02: Question Guide Editor
Test Specification: create, update, reorder, delete, validation.
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
    email = _unique_email()
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePass1", "name": "Admin"},
    )
    assert r.status_code == 201
    return r.json()["access_token"]


@pytest.fixture
def project_id(client, org_admin_token):
    r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "Test Project"},
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_create_question(client, org_admin_token, project_id):
    """POST /questions creates record."""
    r = client.post(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={
            "question_text": "What is your main challenge?",
            "question_type": "open",
            "probing_depth": 3,
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data["id"]
    assert data["question_text"] == "What is your main challenge?"
    assert data["question_type"] == "open"
    assert data["probing_depth"] == 3
    assert data["order_index"] == 0


def test_update_question(client, org_admin_token, project_id):
    """PATCH /questions/{id} updates fields."""
    create_r = client.post(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"question_text": "Original", "question_type": "open", "probing_depth": 2},
    )
    qid = create_r.json()["id"]
    r = client.patch(
        f"/api/v1/projects/{project_id}/questions/{qid}",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"question_text": "Updated text", "probing_depth": 4},
    )
    assert r.status_code == 200
    assert r.json()["question_text"] == "Updated text"
    assert r.json()["probing_depth"] == 4


def test_reorder_questions(client, org_admin_token, project_id):
    """PATCH /reorder recalculates order_index."""
    r1 = client.post(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"question_text": "First", "question_type": "open", "probing_depth": 1},
    )
    r2 = client.post(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"question_text": "Second", "question_type": "open", "probing_depth": 1},
    )
    q1_id = r1.json()["id"]
    q2_id = r2.json()["id"]
    r = client.patch(
        f"/api/v1/projects/{project_id}/questions/reorder",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"question_id": q2_id, "new_index": 0},
    )
    assert r.status_code == 200
    questions = r.json()["questions"]
    order = {q["id"]: q["order_index"] for q in questions}
    assert order[q2_id] == 0
    assert order[q1_id] == 1


def test_delete_question(client, org_admin_token, project_id):
    """DELETE removes question."""
    create_r = client.post(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"question_text": "To delete", "question_type": "open", "probing_depth": 1},
    )
    qid = create_r.json()["id"]
    r = client.delete(
        f"/api/v1/projects/{project_id}/questions/{qid}",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    assert r.status_code == 204
    list_r = client.get(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    ids = [q["id"] for q in list_r.json()["questions"]]
    assert qid not in ids


def test_question_type_validation(client, org_admin_token, project_id):
    """Invalid type rejected."""
    r = client.post(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"question_text": "Q", "question_type": "invalid_type", "probing_depth": 1},
    )
    assert r.status_code in (400, 422)


def test_probing_depth_range_validation(client, org_admin_token, project_id):
    """Depth must be [1,10]."""
    r = client.post(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"question_text": "Q", "question_type": "open", "probing_depth": 0},
    )
    assert r.status_code in (400, 422)
    r2 = client.post(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"question_text": "Q2", "question_type": "open", "probing_depth": 11},
    )
    assert r2.status_code in (400, 422)
