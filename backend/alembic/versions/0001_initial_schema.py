"""Initial schema — complaint sessions, evidence, solutions, feedback, knowledge, users.

Revision ID: 0001
Revises: None
Create Date: 2025-06-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
    )

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_id", sa.String(200), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("source_version", sa.String(100), nullable=False),
        sa.Column("business_type", sa.String(100), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("import_batch_id", sa.String(100), nullable=True),
        sa.Column("effective_at", sa.DateTime, nullable=True),
        sa.Column("expired_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_type", "source_id", "source_version", name="uq_source_version"),
    )

    op.create_table(
        "complaint_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("client_request_id", sa.String(100), unique=True, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="created"),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("complaint_text_masked", sa.Text, nullable=True),
        sa.Column("intent", sa.JSON, nullable=True),
        sa.Column("emotion", sa.String(50), nullable=True),
        sa.Column("entities", sa.JSON, nullable=True),
        sa.Column("confidence", sa.Float, nullable=True),
        sa.Column("workflow_version", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "retrieved_evidence",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("complaint_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_id", sa.String(100), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("chunk_id", sa.String(100), nullable=False),
        sa.Column("source_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content_snapshot", sa.Text, nullable=True),
        sa.Column("score", sa.Float, nullable=False, server_default="0.0"),
        sa.Column("rerank_score", sa.Float, nullable=True),
        sa.Column("metadata", sa.JSON, nullable=True),
        sa.UniqueConstraint("session_id", "evidence_id", name="uq_session_evidence"),
    )

    op.create_table(
        "generated_solutions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("complaint_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("solution_text", sa.Text, nullable=False),
        sa.Column("cited_evidence_ids", sa.JSON, nullable=True),
        sa.Column("assessment", sa.Text, nullable=True),
        sa.Column("steps", sa.JSON, nullable=True),
        sa.Column("risk_notice", sa.Text, nullable=True),
        sa.Column("validation_status", sa.String(20), nullable=True),
        sa.Column("validation_details", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "human_feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("complaint_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("payload_fingerprint", sa.String(200), nullable=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("edited_solution", sa.Text, nullable=True),
        sa.Column("reject_reason", sa.Text, nullable=True),
        sa.Column("operator_note", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("session_id", "idempotency_key", name="uq_session_idempotency"),
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("complaint_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", sa.String(100), unique=True, nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "workflow_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("complaint_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_id", sa.String(100), nullable=False),
        sa.Column("event_id", sa.String(100), nullable=False),
        sa.Column("trace_id", sa.String(100), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("data", sa.JSON, nullable=True),
        sa.Column("sequence", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "feedback_outbox",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), sa.ForeignKey("complaint_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("idempotency_key", sa.String(200), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("feedback_outbox")
    op.drop_table("workflow_events")
    op.drop_table("workflow_runs")
    op.drop_table("human_feedback")
    op.drop_table("generated_solutions")
    op.drop_table("retrieved_evidence")
    op.drop_table("complaint_sessions")
    op.drop_table("knowledge_documents")
    op.drop_table("users")
