"""Add captured source document metadata.

Revision ID: 20260630_0002
Revises: 20260630_0001
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260630_0002"
down_revision: str | None = "20260630_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "source_documents",
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("publisher", sa.String(), nullable=False),
        sa.Column("canonical_url", sa.String(), nullable=False),
        sa.Column("source_identifier", sa.String(), nullable=False),
        sa.Column("published_at", sa.String(), nullable=True),
        sa.Column("retrieved_at", sa.String(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["research_runs.run_id"]),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint(
            "run_id",
            "source_identifier",
            "content_sha256",
            name="uq_source_capture",
        ),
    )
    op.create_index(
        "source_documents_run_id",
        "source_documents",
        ["run_id", "source_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("source_documents_run_id", table_name="source_documents")
    op.drop_table("source_documents")
