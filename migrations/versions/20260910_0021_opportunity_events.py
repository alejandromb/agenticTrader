"""Append-only opportunity research decisions."""

import sqlalchemy as sa
from alembic import op

revision = "20260910_0021"
down_revision = "20260907_0020"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "opportunity_events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("record_json", sa.String(), nullable=False),
        sa.UniqueConstraint("candidate_id", "sequence"),
    )
    op.create_index(
        "ix_opportunity_events_candidate_id", "opportunity_events", ["candidate_id"]
    )


def downgrade():
    op.drop_index("ix_opportunity_events_candidate_id", "opportunity_events")
    op.drop_table("opportunity_events")
