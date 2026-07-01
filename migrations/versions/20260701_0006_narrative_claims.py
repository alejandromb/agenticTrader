"""Allow narrative candidate claims.

Revision ID: 20260701_0006
Revises: 20260701_0005
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0006"
down_revision: str | None = "20260701_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("candidate_claims") as batch_op:
        batch_op.alter_column(
            "numeric_value",
            existing_type=sa.String(),
            nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("candidate_claims") as batch_op:
        batch_op.alter_column(
            "numeric_value",
            existing_type=sa.String(),
            nullable=False,
        )
