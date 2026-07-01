"""Add deterministic decision monitoring ledger."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260701_0016"
down_revision: str | None = "20260701_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "decision_monitors",
        sa.Column("monitor_id", sa.String(), primary_key=True),
        sa.Column(
            "run_id", sa.String(), sa.ForeignKey("research_runs.run_id"), nullable=False
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("rules_sha256", sa.String(64), nullable=False),
        sa.Column("rules_storage_path", sa.String(), nullable=False),
        sa.Column("rules_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
    )
    op.create_table(
        "monitor_evaluations",
        sa.Column("evaluation_id", sa.String(), primary_key=True),
        sa.Column(
            "monitor_id",
            sa.String(),
            sa.ForeignKey("decision_monitors.monitor_id"),
            nullable=False,
        ),
        sa.Column(
            "dataset_id",
            sa.String(),
            sa.ForeignKey("price_datasets.dataset_id"),
            nullable=False,
        ),
        sa.Column("dataset_sha256", sa.String(64), nullable=False),
        sa.Column("as_of", sa.String(), nullable=False),
        sa.Column("results_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.UniqueConstraint(
            "monitor_id", "dataset_id", "as_of", name="uq_monitor_evaluation"
        ),
    )
    op.create_table(
        "monitor_alerts",
        sa.Column("alert_id", sa.String(), primary_key=True),
        sa.Column(
            "evaluation_id",
            sa.String(),
            sa.ForeignKey("monitor_evaluations.evaluation_id"),
            nullable=False,
        ),
        sa.Column(
            "monitor_id",
            sa.String(),
            sa.ForeignKey("decision_monitors.monitor_id"),
            nullable=False,
        ),
        sa.Column("rule_id", sa.String(), nullable=False),
        sa.Column("evidence_json", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=False),
        sa.UniqueConstraint(
            "evaluation_id", "rule_id", name="uq_evaluation_rule_alert"
        ),
    )
    op.create_table(
        "alert_acknowledgements",
        sa.Column("acknowledgement_id", sa.String(), primary_key=True),
        sa.Column(
            "alert_id",
            sa.String(),
            sa.ForeignKey("monitor_alerts.alert_id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("note", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("acknowledged_at", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("alert_acknowledgements")
    op.drop_table("monitor_alerts")
    op.drop_table("monitor_evaluations")
    op.drop_table("decision_monitors")
