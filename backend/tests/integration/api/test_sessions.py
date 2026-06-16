import pytest

USER_ID = "11111111-1111-4111-8111-111111111111"


@pytest.fixture
def test_user(db_session):
    from app.db.models.complaint import User

    existing = db_session.get(User, USER_ID)
    if existing is not None:
        return existing
    user = User(id=USER_ID, name="Test Agent", role="agent")
    db_session.add(user)
    db_session.flush()
    return user


def test_create_session_is_idempotent(client, db_session, test_user):
    headers = {"Idempotency-Key": "client-request-001"}
    payload = {"user_id": USER_ID, "complaint_text": "test complaint 1"}
    first = client.post("/api/v1/complaints/sessions", headers=headers, json=payload)
    assert first.status_code == 201
    second = client.post("/api/v1/complaints/sessions", headers=headers, json=payload)
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_create_session_without_idempotency_key(client, db_session, test_user):
    payload = {"user_id": USER_ID, "complaint_text": "another complaint"}
    response = client.post("/api/v1/complaints/sessions", json=payload)
    assert response.status_code == 201
    assert response.json()["id"] is not None
