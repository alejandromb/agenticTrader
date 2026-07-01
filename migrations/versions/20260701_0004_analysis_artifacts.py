"""Add structured analysis artifacts and input lineage.

Revision ID: 20260701_0004
Revises: 20260630_0003
Create Date: 2026-07-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0004"
down_revision: str | None = "20260630_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("candidate_claims") as batch_op:
        batch_op.create_unique_constraint(
            "uq_candidate_claim_run", ["claim_id", "run_id"]
        )

    op.create_table(
        "analysis_artifacts",
        sa.Column("artifact_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("artifact_type", sa.String(), nullable=False),
        sa.Column("schema_version", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=False),
        sa.Column("provider_response_id", sa.String(), nullable=False),
        sa.Column("prompt_version", sa.String(), nullable=False),
        sa.Column("content_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["research_runs.run_id"]),
        sa.PrimaryKeyConstraint("artifact_id"),
        sa.UniqueConstraint("artifact_id", "run_id", name="uq_analysis_artifact_run"),
        sa.UniqueConstraint("provider_response_id"),
    )
    op.create_index(
        "analysis_artifacts_run_id",
        "analysis_artifacts",
        ["run_id", "artifact_id"],
        unique=False,
    )
    op.create_table(
        "analysis_input_claims",
        sa.Column("artifact_id", sa.String(), nullable=False),
        sa.Column("claim_id", sa.String(), nullable=False),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(
            ["artifact_id", "run_id"],
            ["analysis_artifacts.artifact_id", "analysis_artifacts.run_id"],
            name="fk_analysis_input_artifact_run",
        ),
        sa.ForeignKeyConstraint(
            ["claim_id", "run_id"],
            ["candidate_claims.claim_id", "candidate_claims.run_id"],
            name="fk_analysis_input_claim_run",
        ),
        sa.PrimaryKeyConstraint("artifact_id", "claim_id", "run_id"),
    )


def downgrade() -> None:
    op.drop_table("analysis_input_claims")
    op.drop_index("analysis_artifacts_run_id", table_name="analysis_artifacts")
    op.drop_table("analysis_artifacts")
    with op.batch_alter_table("candidate_claims") as batch_op:
        batch_op.drop_constraint("uq_candidate_claim_run", type_="unique")
