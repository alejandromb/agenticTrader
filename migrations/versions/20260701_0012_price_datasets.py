"""Add immutable point-in-time price datasets."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0012"
down_revision: str | None = "20260701_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "price_datasets",
        sa.Column("dataset_id", sa.String(), primary_key=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("retrieved_at", sa.String(), nullable=False),
        sa.Column("content_sha256", sa.String(64), nullable=False, unique=True),
        sa.Column("storage_path", sa.String(), nullable=False),
        sa.Column("adjustment_note", sa.String(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.String(), nullable=False),
        sa.Column("end_date", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_table(
        "price_observations",
        sa.Column(
            "dataset_id",
            sa.String(),
            sa.ForeignKey("price_datasets.dataset_id"),
            primary_key=True,
        ),
        sa.Column("ticker", sa.String(), primary_key=True),
        sa.Column("date", sa.String(), primary_key=True),
        sa.Column("adjusted_close", sa.String(), nullable=False),
    )
    op.create_index(
        "price_observations_ticker_date",
        "price_observations",
        ["dataset_id", "ticker", "date"],
    )


def downgrade() -> None:
    op.drop_index("price_observations_ticker_date", table_name="price_observations")
    op.drop_table("price_observations")
    op.drop_table("price_datasets")
