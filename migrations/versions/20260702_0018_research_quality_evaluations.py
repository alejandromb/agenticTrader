"""Add append-only research-quality evaluations."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260702_0018"
down_revision: str | None = "20260701_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_quality_evaluations",
        sa.Column("evaluation_id", sa.String(), primary_key=True),
        sa.Column(
            "run_id",
            sa.String(),
            sa.ForeignKey("research_runs.run_id"),
            nullable=False,
        ),
        sa.Column(
            "analysis_artifact_id",
            sa.String(),
            sa.ForeignKey("analysis_artifacts.artifact_id"),
            nullable=False,
        ),
        sa.Column(
            "memo_artifact_id",
            sa.String(),
            sa.ForeignKey("investment_memo_artifacts.artifact_id"),
            nullable=False,
        ),
        sa.Column("rubric_version", sa.String(), nullable=False),
        sa.Column("gates_json", sa.String(), nullable=False),
        sa.Column("scores_json", sa.String(), nullable=False),
        sa.Column("total_score", sa.Integer(), nullable=False),
        sa.Column("accepted", sa.Integer(), nullable=False),
        sa.Column("provenance_json", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_index(
        "research_quality_evaluations_run_id",
        "research_quality_evaluations",
        ["run_id", "created_at", "evaluation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "research_quality_evaluations_run_id",
        table_name="research_quality_evaluations",
    )
    op.drop_table("research_quality_evaluations")
