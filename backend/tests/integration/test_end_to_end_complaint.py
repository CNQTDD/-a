from __future__ import annotations

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
    db_session.commit()
    return user


def test_end_to_end_complaint_flow(client, db_session, test_user):
    create_resp = client.post(
        "/api/v1/complaints/sessions",
        json={"user_id": USER_ID, "complaint_text": "套餐扣费有误，要求核查"},
    )
    assert create_resp.status_code == 201
    session_id = create_resp.json()["id"]

    message_resp = client.post(
        f"/api/v1/complaints/sessions/{session_id}/messages",
        json={"message": "请帮我核查上个月套餐扣费"},
    )
    assert message_resp.status_code == 200
    run_id = message_resp.json()["run_id"]

    events_resp = client.get(
        f"/api/v1/complaints/sessions/{session_id}/events",
        headers={"Last-Event-ID": "evt-0"},
    )
    assert events_resp.status_code == 200
    assert "workflow_started" in events_resp.text
    assert "intent_completed" in events_resp.text
    assert "retrieval_completed" in events_resp.text
    assert "workflow_completed" in events_resp.text

    session_resp = client.get(f"/api/v1/complaints/sessions/{session_id}")
    session_data = session_resp.json()
    assert session_data["solution"]["cited_evidence_ids"]
    assert session_data["validation"]["status"] == "passed"
    assert session_data["status"] == "waiting_human"

    feedback_resp = client.post(
        f"/api/v1/complaints/sessions/{session_id}/feedback",
        json={
            "action": "edited",
            "edited_solution": "已核查完成，费用将在下期账单中退回。",
            "operator_note": "按规则修正",
        },
    )
    assert feedback_resp.status_code == 200
    assert feedback_resp.json()["session_id"] == session_id
    assert feedback_resp.json()["action"] == "edited"

    final_resp = client.get(f"/api/v1/complaints/sessions/{session_id}")
    final_data = final_resp.json()
    assert final_data["status"] == "completed"
    assert final_data["solution"]["solution_text"] == "已核查完成，费用将在下期账单中退回。"
    assert run_id
