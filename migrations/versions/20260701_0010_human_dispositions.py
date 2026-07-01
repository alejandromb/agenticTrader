"""Add append-only human disposition events."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0010"
down_revision: str | None = "20260701_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "human_disposition_events",
        sa.Column("event_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            sa.String(),
            sa.ForeignKey("research_runs.run_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("rationale", sa.String()),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("decided_at", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("human_disposition_events")
