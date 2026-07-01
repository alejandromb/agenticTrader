"""Add deterministic backtest artifacts."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0015"
down_revision: str | None = "20260701_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "backtest_artifacts",
        sa.Column("backtest_id", sa.String(), primary_key=True),
        sa.Column(
            "dataset_id",
            sa.String(),
            sa.ForeignKey("price_datasets.dataset_id"),
            nullable=False,
        ),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("benchmark", sa.String(), nullable=False),
        sa.Column("strategy", sa.String(), nullable=False),
        sa.Column("strategy_version", sa.String(), nullable=False),
        sa.Column("parameters_json", sa.String(), nullable=False),
        sa.Column("results_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("backtest_artifacts")
