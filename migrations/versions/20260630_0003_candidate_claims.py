"""Add evidence-linked candidate claims.

Revision ID: 20260630_0003
Revises: 20260630_0002
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260630_0003"
down_revision: str | None = "20260630_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("source_documents") as batch_op:
        batch_op.create_unique_constraint(
            "uq_source_document_run", ["source_id", "run_id"]
        )

    op.create_table(
        "candidate_claims",
        sa.Column("claim_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("claim_type", sa.String(), nullable=False),
        sa.Column("statement", sa.String(), nullable=False),
        sa.Column("taxonomy", sa.String(), nullable=False),
        sa.Column("concept", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("numeric_value", sa.String(), nullable=False),
        sa.Column("period_start", sa.String(), nullable=True),
        sa.Column("period_end", sa.String(), nullable=False),
        sa.Column("accession_number", sa.String(), nullable=False),
        sa.Column("extraction_method", sa.String(), nullable=False),
        sa.Column("extracted_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id", "run_id"],
            ["source_documents.source_id", "source_documents.run_id"],
            name="fk_candidate_claim_source_run",
        ),
        sa.PrimaryKeyConstraint("claim_id"),
        sa.UniqueConstraint(
            "run_id",
            "source_id",
            "taxonomy",
            "concept",
            "unit",
            "period_end",
            name="uq_candidate_fact_observation",
        ),
    )
    op.create_index(
        "candidate_claims_run_id",
        "candidate_claims",
        ["run_id", "claim_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("candidate_claims_run_id", table_name="candidate_claims")
    op.drop_table("candidate_claims")
    with op.batch_alter_table("source_documents") as batch_op:
        batch_op.drop_constraint("uq_source_document_run", type_="unique")
