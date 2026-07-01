"""Create research runs and transition events.

Revision ID: 20260630_0001
Revises:
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260630_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_runs",
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("memo_id", sa.String(), nullable=False),
        sa.Column("workflow_version", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("as_of", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.Column("updated_at", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("run_id"),
        sa.UniqueConstraint("memo_id"),
    )
    op.create_table(
        "transition_events",
        sa.Column("event_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("from_state", sa.String(), nullable=True),
        sa.Column("to_state", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.String(), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["research_runs.run_id"]),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "transition_events_run_id",
        "transition_events",
        ["run_id", "event_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("transition_events_run_id", table_name="transition_events")
    op.drop_table("transition_events")
    op.drop_table("research_runs")
