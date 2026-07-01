"""Add canonical investment memo artifacts."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0009"
down_revision: str | None = "20260701_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investment_memo_artifacts",
        sa.Column("artifact_id", sa.String(), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(),
            sa.ForeignKey("research_runs.run_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "analysis_artifact_id",
            sa.String(),
            sa.ForeignKey("analysis_artifacts.artifact_id"),
            nullable=False,
        ),
        sa.Column("schema_version", sa.String(), nullable=False),
        sa.Column("content_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("investment_memo_artifacts")
