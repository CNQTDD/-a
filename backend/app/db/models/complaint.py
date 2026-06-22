from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    sessions: Mapped[list["ComplaintSession"]] = relationship(back_populates="user")


class ComplaintSession(Base):
    __tablename__ = "complaint_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    client_request_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="created")
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    complaint_text_masked: Mapped[str | None] = mapped_column(Text, nullable=True)
    intent: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entities: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    workflow_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="sessions")
    evidence: Mapped[list["RetrievedEvidence"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by=lambda: (
            RetrievedEvidence.rerank_score.desc(),
            RetrievedEvidence.score.desc(),
            RetrievedEvidence.id.asc(),
        ),
    )
    solutions: Mapped[list["GeneratedSolution"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["HumanFeedback"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )

    __table_args__ = ({"sqlite_autoincrement": True},)


class RetrievedEvidence(Base):
    __tablename__ = "retrieved_evidence"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("complaint_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[str] = mapped_column(String(100), nullable=False)
    chunk_id: Mapped[str] = mapped_column(String(100), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rerank_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    session: Mapped["ComplaintSession"] = relationship(back_populates="evidence")

    __table_args__ = (
        UniqueConstraint("session_id", "evidence_id", name="uq_session_evidence"),
        {"sqlite_autoincrement": True},
    )


class GeneratedSolution(Base):
    __tablename__ = "generated_solutions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("complaint_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    solution_text: Mapped[str] = mapped_column(Text, nullable=False)
    cited_evidence_ids: Mapped[list | None] = mapped_column(JSON, nullable=True)
    assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    steps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risk_notice: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    validation_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    session: Mapped["ComplaintSession"] = relationship(back_populates="solutions")


class HumanFeedback(Base):
    __tablename__ = "human_feedback"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("complaint_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    payload_fingerprint: Mapped[str | None] = mapped_column(String(200), nullable=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    edited_solution: Mapped[str | None] = mapped_column(Text, nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    operator_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    session: Mapped["ComplaintSession"] = relationship(back_populates="feedback")

    __table_args__ = (
        UniqueConstraint(
            "session_id", "idempotency_key", name="uq_session_idempotency"
        ),
        {"sqlite_autoincrement": True},
    )


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    source_id: Mapped[str] = mapped_column(String(200), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_version: Mapped[str] = mapped_column(String(100), nullable=False)
    business_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    import_batch_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expired_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "source_type", "source_id", "source_version", name="uq_source_version"
        ),
        {"sqlite_autoincrement": True},
    )
