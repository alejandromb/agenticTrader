"""Persist immutable portfolio snapshot references."""

import sqlalchemy as sa
from alembic import op

revision = "20260907_0019"
down_revision = "20260702_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portfolio_snapshots",
        sa.Column("snapshot_id", sa.String(), primary_key=True),
        sa.Column("account_ref", sa.String(), nullable=False),
        sa.Column("collected_at", sa.String(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False),
        sa.Column("coverage", sa.String(), nullable=False),
    )
    op.create_index(
        "ix_portfolio_snapshots_account_ref", "portfolio_snapshots", ["account_ref"]
    )


def downgrade() -> None:
    op.drop_index("ix_portfolio_snapshots_account_ref", "portfolio_snapshots")
    op.drop_table("portfolio_snapshots")
