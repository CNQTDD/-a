from sqlalchemy import text

from app.db.models.complaint import (
    ComplaintSession,
    GeneratedSolution,
    HumanFeedback,
    RetrievedEvidence,
    User,
)


def test_create_user(db_session):
    user = User(id="u-1", name="Test Agent", role="agent", status="active")
    db_session.add(user)
    db_session.commit()

    found = db_session.get(User, "u-1")
    assert found is not None
    assert found.name == "Test Agent"


def test_create_session_with_evidence_and_solutions(db_session):
    user = User(id="u-2", name="Test Agent", role="agent")
    db_session.add(user)
    db_session.commit()

    session = ComplaintSession(
        id="s-1",
        user_id="u-2",
        complaint_text_masked="套餐变更问题，**138****5678**",
        status="created",
    )
    db_session.add(session)
    db_session.commit()

    evidence = RetrievedEvidence(
        id="ev-1",
        session_id="s-1",
        evidence_id="chunk:rule-101",
        source_id="rule-101",
        chunk_id="rule-101-chunk-1",
        source_type="business_rule",
        title="套餐变更规则",
        content_snapshot="用户可在合约期内变更套餐，但需支付差价。",
        score=0.85,
    )
    db_session.add(evidence)

    solution = GeneratedSolution(
        id="sol-1",
        session_id="s-1",
        solution_text="建议按规则处理套餐变更。",
        model_version="Qwen2.5-14B",
        validation_status="passed",
    )
    db_session.add(solution)

    feedback = HumanFeedback(
        id="fb-1",
        session_id="s-1",
        idempotency_key="key-001",
        action="accepted",
    )
    db_session.add(feedback)
    db_session.commit()

    # Verify cascade on session delete
    db_session.delete(session)
    db_session.commit()

    assert db_session.get(RetrievedEvidence, "ev-1") is None
    assert db_session.get(GeneratedSolution, "sol-1") is None
    assert db_session.get(HumanFeedback, "fb-1") is None
    # User not affected by session cascade
    assert db_session.get(User, "u-2") is not None


def test_feedback_idempotency_constraint(db_session):
    user = User(id="u-3", name="Test Agent", role="agent")
    db_session.add(user)
    db_session.commit()

    session = ComplaintSession(id="s-2", user_id="u-3", complaint_text_masked="test")
    db_session.add(session)
    db_session.commit()

    fb1 = HumanFeedback(
        id="fb-a",
        session_id="s-2",
        idempotency_key="key-001",
        action="accepted",
    )
    db_session.add(fb1)
    db_session.commit()

    fb2 = HumanFeedback(
        id="fb-b",
        session_id="s-2",
        idempotency_key="key-001",
        action="rejected",
        reject_reason="duplicate test",
    )

    import pytest
    from sqlalchemy.exc import IntegrityError

    db_session.add(fb2)
    with pytest.raises(IntegrityError):
        db_session.commit()
