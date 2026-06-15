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


def test_list_sessions_returns_user_scoped(client, db_session, test_user):
    # Create multiple sessions
    for i in range(3):
        payload = {"user_id": USER_ID, "complaint_text": f"投诉 #{i}"}
        client.post("/api/v1/complaints/sessions", json=payload)

    response = client.get(
        "/api/v1/complaints/sessions",
        params={"user_id": USER_ID, "limit": 20},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 3
    for item in data["items"]:
        assert item["user_id"] == USER_ID


def test_list_sessions_cursor_pagination(client, db_session, test_user):
    # Create sessions
    ids = []
    for i in range(5):
        payload = {"user_id": USER_ID, "complaint_text": f"分页投诉 #{i}"}
        resp = client.post("/api/v1/complaints/sessions", json=payload)
        ids.append(resp.json()["id"])

    # First page
    resp1 = client.get(
        "/api/v1/complaints/sessions",
        params={"user_id": USER_ID, "limit": 2},
    )
    data1 = resp1.json()
    assert len(data1["items"]) == 2
    assert data1["cursor"] is not None

    # Second page
    resp2 = client.get(
        "/api/v1/complaints/sessions",
        params={"user_id": USER_ID, "limit": 2, "cursor": data1["cursor"]},
    )
    data2 = resp2.json()
    assert len(data2["items"]) == 2

    # No overlap between pages
    page1_ids = {item["id"] for item in data1["items"]}
    page2_ids = {item["id"] for item in data2["items"]}
    assert page1_ids.isdisjoint(page2_ids)
