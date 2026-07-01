"""Add visible cross-filing revision audits."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0007"
down_revision: str | None = "20260701_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "revision_audits",
        sa.Column("audit_id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), sa.ForeignKey("research_runs.run_id")),
        sa.Column("classification", sa.String(), nullable=False),
        sa.Column("concept", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("period_start", sa.String()),
        sa.Column("period_end", sa.String(), nullable=False),
        sa.Column("original_accession", sa.String(), nullable=False),
        sa.Column("original_value", sa.String(), nullable=False),
        sa.Column("later_accession", sa.String(), nullable=False),
        sa.Column("later_value", sa.String(), nullable=False),
        sa.Column("absolute_change", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_index("revision_audits_run_id", "revision_audits", ["run_id", "audit_id"])


def downgrade() -> None:
    op.drop_index("revision_audits_run_id", table_name="revision_audits")
    op.drop_table("revision_audits")
