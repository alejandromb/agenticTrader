"""Retain portfolio collection outcomes independently of snapshot content."""

import sqlalchemy as sa
from alembic import op

revision = "20260907_0020"
down_revision = "20260907_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "portfolio_refreshes",
        sa.Column("refresh_id", sa.String(), primary_key=True),
        sa.Column("account_ref", sa.String(), nullable=False),
        sa.Column(
            "snapshot_id", sa.String(), sa.ForeignKey("portfolio_snapshots.snapshot_id")
        ),
        sa.Column("record_json", sa.String(), nullable=False),
    )
    op.create_index(
        "ix_portfolio_refreshes_account_ref", "portfolio_refreshes", ["account_ref"]
    )


def downgrade() -> None:
    op.drop_index("ix_portfolio_refreshes_account_ref", "portfolio_refreshes")
    op.drop_table("portfolio_refreshes")
