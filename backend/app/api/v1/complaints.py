from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import Settings
from app.db.repositories.complaints import ComplaintRepository
from app.domain.schemas import FeedbackCreate, SessionCreate
from app.workflow.service import ComplaintWorkflowService

router = APIRouter(prefix="/complaints", tags=["complaints"])


def _repo(db: Session) -> ComplaintRepository:
    return ComplaintRepository(db)


def _workflow(db: Session, settings: Settings) -> ComplaintWorkflowService:
    return ComplaintWorkflowService(db, settings=settings)


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


@router.get("/{session_id}")
async def get_session_alias(
    session_id: str,
    db: Session = Depends(get_db),
):
    return await get_session(session_id=session_id, db=db)


@router.post("/sessions/{session_id}/messages")
async def post_message(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    repo = _repo(db)
    session = repo.get_by_id(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    payload = await request.json()
    run_id = await _workflow(db, request.app.state.settings).start_run(
        session,
        payload.get("message", ""),
        request.headers.get("X-Request-ID"),
    )
    return {"run_id": run_id}


@router.post("/{session_id}/messages")
async def post_message_alias(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    return await post_message(session_id=session_id, request=request, db=db)


@router.get("/sessions/{session_id}/events")
async def get_events(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    repo = _repo(db)
    session = repo.get_by_id(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    body = _workflow(
        db,
        request.app.state.settings,
    ).stream_events(session_id, request.headers.get("Last-Event-ID"))
    return PlainTextResponse(body, media_type="text/event-stream")


@router.post("/sessions/{session_id}/feedback")
async def submit_feedback(
    session_id: str,
    payload: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    repo = _repo(db)
    session = repo.get_by_id(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    feedback = _workflow(db, request.app.state.settings).apply_feedback(
        session,
        action=payload.action.value,
        edited_solution=payload.edited_solution,
        reject_reason=payload.reject_reason,
        operator_note=payload.operator_note,
        idempotency_key=request.headers.get("Idempotency-Key") or str(uuid.uuid4()),
    )
    return {
        "id": feedback.id,
        "session_id": feedback.session_id,
        "action": feedback.action,
        "edited_solution": feedback.edited_solution,
        "reject_reason": feedback.reject_reason,
        "operator_note": feedback.operator_note,
        "created_at": feedback.created_at,
    }


@router.post("/{session_id}/feedback")
async def submit_feedback_alias(
    session_id: str,
    payload: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    return await submit_feedback(session_id=session_id, payload=payload, request=request, db=db)


@router.get("/{session_id}/events")
async def get_events_alias(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    return await get_events(session_id=session_id, request=request, db=db)
