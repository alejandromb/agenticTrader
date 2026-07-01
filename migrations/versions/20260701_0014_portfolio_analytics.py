"""Add hypothetical portfolio analysis artifacts."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0014"
down_revision: str | None = "20260701_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "portfolio_analysis_artifacts",
        sa.Column("analysis_id", sa.String(), primary_key=True),
        sa.Column(
            "dataset_id",
            sa.String(),
            sa.ForeignKey("price_datasets.dataset_id"),
            nullable=False,
        ),
        sa.Column("as_of", sa.String(), nullable=False),
        sa.Column("valuation_date", sa.String(), nullable=False),
        sa.Column("benchmark", sa.String(), nullable=False),
        sa.Column("holdings_sha256", sa.String(64), nullable=False),
        sa.Column("holdings_storage_path", sa.String(), nullable=False),
        sa.Column("holdings_json", sa.String(), nullable=False),
        sa.Column("results_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("portfolio_analysis_artifacts")
