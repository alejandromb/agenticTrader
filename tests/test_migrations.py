from __future__ import annotations

import sqlite3
from pathlib import Path

from agentic_trading.migrations import upgrade_database


def test_upgrade_database_creates_versioned_schema(tmp_path: Path) -> None:
    database = tmp_path / "state" / "agentic-trading.db"

    upgrade_database(database)

    with sqlite3.connect(database) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        version = connection.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()

    assert {
        "alembic_version",
        "analysis_artifacts",
        "analysis_input_claims",
        "candidate_claims",
        "calculation_claims",
        "calculation_input_claims",
        "investment_memo_artifacts",
        "human_disposition_events",
        "price_datasets",
        "price_observations",
        "research_screen_artifacts",
        "portfolio_analysis_artifacts",
        "backtest_artifacts",
        "research_runs",
        "revision_audits",
        "source_documents",
        "transition_events",
    } <= tables
    assert version == ("20260701_0015",)
