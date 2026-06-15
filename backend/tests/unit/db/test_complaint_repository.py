import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.repositories.complaints import ComplaintRepository
from app.db.models.complaint import ComplaintSession, User
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
