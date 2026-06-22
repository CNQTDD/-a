"""Fix retrieved evidence uniqueness for existing databases.

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-18
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    unique_constraints = {
        item["name"] for item in inspector.get_unique_constraints("retrieved_evidence")
    }
    indexes = {item["name"]: item for item in inspector.get_indexes("retrieved_evidence")}

    if "evidence_id" in unique_constraints:
        op.drop_constraint("evidence_id", "retrieved_evidence", type_="unique")
    elif indexes.get("evidence_id", {}).get("unique"):
        op.drop_index("evidence_id", table_name="retrieved_evidence")

    if "uq_session_evidence" not in unique_constraints:
        op.create_unique_constraint(
            "uq_session_evidence",
            "retrieved_evidence",
            ["session_id", "evidence_id"],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    unique_constraints = {
        item["name"] for item in inspector.get_unique_constraints("retrieved_evidence")
    }

    if "uq_session_evidence" in unique_constraints:
        op.drop_constraint("uq_session_evidence", "retrieved_evidence", type_="unique")

    if "evidence_id" not in unique_constraints:
        op.create_unique_constraint(
            "evidence_id",
            "retrieved_evidence",
            ["evidence_id"],
        )
