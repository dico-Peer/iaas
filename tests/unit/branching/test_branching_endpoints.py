"""
US-2.03: Branching Logic Builder
Test Specification: PATCH /questions/{id}/branching stores correct schema.
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
def project_with_questions(client, org_admin_token):
    r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={"title": "Branching Project"},
    )
    assert r.status_code == 201
    project_id = r.json()["id"]
    for i, text in enumerate(["First", "Second", "Third"]):
        qr = client.post(
            f"/api/v1/projects/{project_id}/questions",
            headers={"Authorization": f"Bearer {org_admin_token}"},
            json={"question_text": text, "question_type": "open", "probing_depth": 2},
        )
        assert qr.status_code == 201
    list_r = client.get(
        f"/api/v1/projects/{project_id}/questions",
        headers={"Authorization": f"Bearer {org_admin_token}"},
    )
    questions = list_r.json()["questions"]
    return project_id, questions


def test_branching_saved_as_jsonb(client, org_admin_token, project_with_questions):
    """PATCH /questions/{id}/branching stores correct schema."""
    project_id, questions = project_with_questions
    q1_id = questions[0]["id"]
    q2_id = questions[1]["id"]
    r = client.patch(
        f"/api/v1/projects/{project_id}/questions/{q1_id}/branching",
        headers={"Authorization": f"Bearer {org_admin_token}"},
        json={
            "rules": [
                {
                    "condition_type": "answer_contains_text",
                    "condition_value": "love",
                    "logic_operator": "AND",
                    "target_question_id": q2_id,
                }
            ],
            "default_next_question_id": questions[2]["id"],
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert "branching_rules" in data
    br = data["branching_rules"]
    assert "rules" in br
    assert len(br["rules"]) == 1
    assert br["rules"][0]["condition_type"] == "answer_contains_text"
    assert br["rules"][0]["condition_value"] == "love"
    assert br["rules"][0]["target_question_id"] == q2_id
    assert br["default_next_question_id"] == questions[2]["id"]
