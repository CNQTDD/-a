from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.db.repositories.complaints import ComplaintRepository
from app.domain.schemas import SessionCreate

router = APIRouter(prefix="/complaints", tags=["complaints"])


def _repo(db: Session) -> ComplaintRepository:
    return ComplaintRepository(db)


@router.post("/sessions")
async def create_session(
    payload: SessionCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    repo = _repo(db)
    idempotency_key = request.headers.get("Idempotency-Key")

    # Check for existing session by idempotency key
    if idempotency_key:
        from app.db.models.complaint import ComplaintSession

        existing = (
            db.query(ComplaintSession)
            .filter_by(client_request_id=idempotency_key)
            .first()
        )
        if existing:
            response.status_code = 200
            return repo.to_response(existing).model_dump()

    payload_clean = SessionCreate(
        user_id=payload.user_id,
        complaint_text=payload.complaint_text,
        client_request_id=idempotency_key,
    )
    session, is_new = repo.create_or_get(payload_clean)
    response.status_code = 201 if is_new else 200
    return repo.to_response(session).model_dump()


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    repo = _repo(db)
    session = repo.get_by_id(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return repo.to_response(session).model_dump()


@router.get("/sessions")
async def list_sessions(
    user_id: str,
    limit: int = 20,
    cursor: str | None = None,
    db: Session = Depends(get_db),
):
    repo = _repo(db)
    return repo.list_by_user(user_id, limit, cursor).model_dump()
