"""Add model token usage and latency to analysis artifacts."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0011"
down_revision: str | None = "20260701_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("analysis_artifacts") as batch_op:
        batch_op.add_column(sa.Column("input_tokens", sa.Integer()))
        batch_op.add_column(sa.Column("output_tokens", sa.Integer()))
        batch_op.add_column(sa.Column("request_duration_ms", sa.Integer()))


def downgrade() -> None:
    with op.batch_alter_table("analysis_artifacts") as batch_op:
        batch_op.drop_column("request_duration_ms")
        batch_op.drop_column("output_tokens")
        batch_op.drop_column("input_tokens")
