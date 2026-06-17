from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Sequence

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.complaint import ComplaintSession
from app.domain.schemas import (
    SessionCreate,
    SessionListItem,
    SessionListResponse,
    SessionResponse,
    ValidationResult,
)


class ComplaintRepository:
    def __init__(self, session: Session):
        self._session = session

    def create_or_get(self, payload: SessionCreate) -> tuple[ComplaintSession, bool]:
        """Create a new session or return an existing one by client_request_id."""
        session_id = str(uuid.uuid4())
        complaint = ComplaintSession(
            id=session_id,
            user_id=payload.user_id,
            client_request_id=payload.client_request_id,
            complaint_text_masked=payload.complaint_text,
            status="created",
        )
        self._session.add(complaint)
        try:
            self._session.commit()
            return complaint, True  # created
        except IntegrityError:
            self._session.rollback()
            if payload.client_request_id:
                existing = (
                    self._session.query(ComplaintSession)
                    .filter_by(client_request_id=payload.client_request_id)
                    .first()
                )
                if existing:
                    return existing, False  # existing
            raise

    def get_by_id(self, session_id: str) -> ComplaintSession | None:
        return self._session.get(ComplaintSession, session_id)

    def claim_run(self, session_id: str, run_id: str) -> bool:
        """Atomically transition session from 'created' to 'running'.

        Returns True if the claim succeeded, False otherwise.
        """
        result = self._session.execute(
            update(ComplaintSession)
            .where(
                ComplaintSession.id == session_id,
                ComplaintSession.status == "created",
            )
            .values(status="running", updated_at=_utc_now())
        )
        self._session.commit()
        return result.rowcount == 1

    def update_status(self, session_id: str, status: str) -> ComplaintSession | None:
        session = self.get_by_id(session_id)
        if session is None:
            return None
        session.status = status
        session.updated_at = _utc_now()
        self._session.commit()
        return session

    def list_by_user(
        self,
        user_id: str,
        limit: int = 20,
        cursor: str | None = None,
    ) -> SessionListResponse:
        query = self._session.query(ComplaintSession).filter(
            ComplaintSession.user_id == user_id
        )
        if cursor:
            query = query.filter(ComplaintSession.id < cursor)
        query = query.order_by(ComplaintSession.id.desc()).limit(limit + 1)

        results: Sequence[ComplaintSession] = query.all()
        has_more = len(results) > limit
        items = results[:limit]

        session_items: list[SessionListItem] = []
        for s in items:
            intent_summary = None
            if s.intent and isinstance(s.intent, dict):
                intent_summary = s.intent.get("intent")
            session_items.append(
                SessionListItem(
                    id=s.id,
                    user_id=s.user_id,
                    status=s.status,
                    risk_level=s.risk_level,
                    intent_summary=intent_summary,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )

        next_cursor = items[-1].id if has_more and items else None
        return SessionListResponse(items=session_items, cursor=next_cursor)

    def to_response(self, session: ComplaintSession) -> SessionResponse:
        evidence = []
        for ev in session.evidence:
            from app.domain.schemas import RetrievedEvidenceItem

            evidence.append(
                RetrievedEvidenceItem(
                    evidence_id=ev.evidence_id,
                    source_id=ev.source_id,
                    chunk_id=ev.chunk_id,
                    source_type=ev.source_type,
                    title=ev.title,
                    content_snapshot=ev.content_snapshot or "",
                    score=ev.score,
                    rerank_score=ev.rerank_score,
                    metadata=ev.metadata_ or {},
                )
            )

        solution_data = None
        if session.solutions:
            latest = sorted(
                session.solutions, key=lambda s: s.created_at or datetime.min
            )[-1]
            from app.domain.schemas import GeneratedSolution

            solution_data = GeneratedSolution(
                solution_text=latest.solution_text,
                cited_evidence_ids=latest.cited_evidence_ids or [],
                assessment=latest.assessment or "",
                steps=latest.steps or [],
                risk_notice=latest.risk_notice or "",
            )

        validation = None
        if solution_data and latest.validation_status:
            details = latest.validation_details or {}
            validation = ValidationResult(
                status=latest.validation_status,
                reason_codes=details.get("reason_codes", []),
                risk_level=session.risk_level or "low",
                recommended_route=details.get("recommended_route", "human_review"),
            )

        return SessionResponse(
            id=session.id,
            user_id=session.user_id,
            status=session.status,
            risk_level=session.risk_level,
            intent=session.intent,
            entities=session.entities,
            confidence=session.confidence,
            evidence=evidence,
            solution=solution_data,
            validation=validation,
            created_at=session.created_at,
            updated_at=session.updated_at,
        )


def _utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
