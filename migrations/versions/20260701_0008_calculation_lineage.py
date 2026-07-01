"""Add formula and input-claim lineage for calculated claims."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0008"
down_revision: str | None = "20260701_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "calculation_claims",
        sa.Column("claim_id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), primary_key=True),
        sa.Column("formula", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["claim_id", "run_id"],
            ["candidate_claims.claim_id", "candidate_claims.run_id"],
            name="fk_calculation_claim_candidate",
        ),
    )
    op.create_table(
        "calculation_input_claims",
        sa.Column("calculation_claim_id", sa.String(), primary_key=True),
        sa.Column("input_claim_id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), primary_key=True),
        sa.ForeignKeyConstraint(
            ["calculation_claim_id", "run_id"],
            ["calculation_claims.claim_id", "calculation_claims.run_id"],
            name="fk_calculation_input_calculation",
        ),
        sa.ForeignKeyConstraint(
            ["input_claim_id", "run_id"],
            ["candidate_claims.claim_id", "candidate_claims.run_id"],
            name="fk_calculation_input_claim",
        ),
    )


def downgrade() -> None:
    op.drop_table("calculation_input_claims")
    op.drop_table("calculation_claims")
