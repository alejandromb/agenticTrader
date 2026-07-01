"""Add persisted deterministic research screens."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0013"
down_revision: str | None = "20260701_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "research_screen_artifacts",
        sa.Column("screen_id", sa.String(), primary_key=True),
        sa.Column("as_of", sa.String(), nullable=False),
        sa.Column("filters_json", sa.String(), nullable=False),
        sa.Column("results_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("research_screen_artifacts")
