import pytest


USER_ID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture
def test_user(db_session):
    from app.db.models.complaint import User
    existing = db_session.get(User, USER_ID)
    if existing:
        return existing
    user = User(id=USER_ID, name="Test Agent", role="agent")
    db_session.add(user)
    db_session.commit()
    return user


def test_get_session_returns_404_for_unknown(client):
    response = client.get("/api/v1/complaints/sessions/nonexistent-id")
    assert response.status_code == 404


def test_get_session_returns_session_data(client, db_session, test_user):
    # First create a session
    payload = {"user_id": USER_ID, "complaint_text": "查询会话"}
    create_resp = client.post("/api/v1/complaints/sessions", json=payload)
    session_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/complaints/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == session_id
    assert data["status"] == "created"


def test_get_session_does_not_return_raw_complaint_text(client, db_session, test_user):
    payload = {"user_id": USER_ID, "complaint_text": "13812345678投诉"}
    create_resp = client.post("/api/v1/complaints/sessions", json=payload)
    session_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/complaints/sessions/{session_id}")
    data = response.json()
    # The response should not contain "complaint_text" key
    assert "complaint_text" not in data
