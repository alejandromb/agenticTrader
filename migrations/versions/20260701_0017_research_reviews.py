"""Add deterministic research-refresh reviews."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0017"
down_revision: str | None = "20260701_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_reviews",
        sa.Column("review_id", sa.String(), primary_key=True),
        sa.Column(
            "baseline_run_id",
            sa.String(),
            sa.ForeignKey("research_runs.run_id"),
            nullable=False,
        ),
        sa.Column(
            "current_run_id",
            sa.String(),
            sa.ForeignKey("research_runs.run_id"),
            nullable=False,
        ),
        sa.Column(
            "baseline_memo_id",
            sa.String(),
            sa.ForeignKey("investment_memo_artifacts.artifact_id"),
            nullable=False,
        ),
        sa.Column(
            "current_memo_id",
            sa.String(),
            sa.ForeignKey("investment_memo_artifacts.artifact_id"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("content_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.UniqueConstraint(
            "baseline_run_id", "current_run_id", name="uq_research_review_pair"
        ),
    )
    op.create_table(
        "research_review_outcomes",
        sa.Column("outcome_id", sa.String(), primary_key=True),
        sa.Column(
            "review_id",
            sa.String(),
            sa.ForeignKey("research_reviews.review_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("outcome", sa.String(), nullable=False),
        sa.Column("rationale", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("recorded_at", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("research_review_outcomes")
    op.drop_table("research_reviews")
