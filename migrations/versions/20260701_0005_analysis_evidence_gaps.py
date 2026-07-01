"""Persist known evidence gaps with analysis artifacts.

Revision ID: 20260701_0005
Revises: 20260701_0004
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0005"
down_revision: str | None = "20260701_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("analysis_artifacts") as batch_op:
        batch_op.add_column(
            sa.Column(
                "evidence_gaps_json",
                sa.String(),
                nullable=False,
                server_default="[]",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("analysis_artifacts") as batch_op:
        batch_op.drop_column("evidence_gaps_json")
