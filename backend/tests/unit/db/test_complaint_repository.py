from sqlalchemy.orm import Session

from app.db.models.complaint import (
    ComplaintSession,
    GeneratedSolution,
    RetrievedEvidence,
    User,
)
from app.db.repositories.complaints import ComplaintRepository
from app.domain.schemas import SessionCreate


def test_claim_run_is_atomic(db_session: Session):
    user = User(id="ru-atomic", name="Atomic Tester", role="agent")
    db_session.add(user)
    db_session.commit()

    repo = ComplaintRepository(db_session)
    payload = SessionCreate(
        user_id="ru-atomic",
        complaint_text="test atomic claim",
        client_request_id="atomic-1",
    )
    session, created = repo.create_or_get(payload)
    assert created

    # First claim: should succeed
    claimed = repo.claim_run(session.id, "run-1")
    assert claimed is True

    # Second claim on same (now running) session: should fail
    claimed2 = repo.claim_run(session.id, "run-2")
    assert claimed2 is False

    # Verify status
    refreshed = db_session.get(ComplaintSession, session.id)
    assert refreshed is not None
    assert refreshed.status == "running"


def test_to_response_includes_solution_validation(db_session: Session):
    user = User(id="ru-validation", name="Validation Tester", role="agent")
    db_session.add(user)
    session = ComplaintSession(
        id="session-validation",
        user_id=user.id,
        status="waiting_human",
        risk_level="high",
        complaint_text_masked="客户要求退费。",
    )
    db_session.add(session)
    db_session.add(
        GeneratedSolution(
            session_id=session.id,
            solution_text="建议核实后退费。",
            validation_status="failed",
            validation_details={"reason_codes": ["missing_evidence"]},
        )
    )
    db_session.commit()

    response = ComplaintRepository(db_session).to_response(session)

    assert response.validation is not None
    assert response.validation.status == "failed"
    assert response.validation.risk_level == "high"


def test_to_response_accepts_sample_complaint_evidence(db_session: Session):
    user = User(id="ru-sample-evidence", name="Evidence Tester", role="agent")
    db_session.add(user)
    session = ComplaintSession(
        id="session-sample-evidence",
        user_id=user.id,
        status="waiting_human",
        complaint_text_masked="网络异常导致客户投诉",
    )
    db_session.add(session)
    db_session.add(
        RetrievedEvidence(
            id="ev-sample-1",
            session_id=session.id,
            evidence_id="sample-complaint-1",
            source_id="sample-complaint-1",
            chunk_id="sample-complaint-1-chunk-1",
            source_type="sample_complaint",
            title="历史样例投诉",
            content_snapshot="用户反馈网络故障影响经营并要求赔偿。",
            score=0.92,
            rerank_score=0.95,
            metadata_={"business_type": "网络故障"},
        )
    )
    db_session.commit()

    response = ComplaintRepository(db_session).to_response(session)

    assert response.evidence[0].source_type == "sample_complaint"
