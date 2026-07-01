from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_trading.cli import main
from agentic_trading.migrations import upgrade_database
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.workflow import WorkflowState

ROOT = Path(__file__).parents[1]
PRICE_FIXTURE = ROOT / "tests/fixtures/prices-valid.csv"
BACKTEST_PRICE_FIXTURE = ROOT / "tests/fixtures/prices-backtest.csv"
HOLDINGS_FIXTURE = ROOT / "tests/fixtures/holdings-valid.csv"


def test_validate_memo_command(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "validate-memo",
            str(ROOT / "examples/investment-memos/aapl-2025-example.json"),
            "--schema",
            str(ROOT / "schemas/investment-memo-v1.schema.json"),
        ]
    )

    assert exit_code == 0
    assert "Valid investment memo" in capsys.readouterr().out


def test_create_and_transition_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "state.db"
    assert (
        main(
            [
                "create-run",
                str(database),
                "memo-001",
                "2025-10-31T23:59:59Z",
            ]
        )
        == 0
    )
    created = json.loads(capsys.readouterr().out)

    assert (
        main(
            [
                "transition",
                str(database),
                created["run_id"],
                "draft",
                "collecting_evidence",
                "--reason",
                "collection_started",
            ]
        )
        == 0
    )
    transitioned = json.loads(capsys.readouterr().out)
    assert transitioned["state"] == "collecting_evidence"


def test_sec_command_requires_user_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SEC_USER_AGENT", "")

    with pytest.raises(SystemExit, match="SEC_USER_AGENT is required"):
        main(["sec-filings", "320193", "--form", "10-K"])


def test_doctor_never_prints_secret_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    database = tmp_path / "state.db"
    database.touch()
    monkeypatch.setenv("OPENAI_API_KEY", "private-openai-value")
    monkeypatch.setenv("SEC_USER_AGENT", "private-sec-value")

    assert main(["doctor", "--database", str(database)]) == 0

    output = capsys.readouterr().out
    assert "private-openai-value" not in output
    assert "private-sec-value" not in output
    assert json.loads(output) == {
        "database_exists": True,
        "openai_api_key_configured": True,
        "sec_user_agent_configured": True,
    }


def test_list_and_show_saved_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "state.db"
    main(
        [
            "create-run",
            str(database),
            "memo-001",
            "2025-10-31T23:59:59Z",
        ]
    )
    created = json.loads(capsys.readouterr().out)

    assert main(["list-runs", "--database", str(database)]) == 0
    assert created["run_id"] in capsys.readouterr().out

    assert main(["show-run", created["run_id"], "--database", str(database)]) == 0
    output = capsys.readouterr().out
    assert "State: draft" in output
    assert "Cross-filing revision audits: 0" in output
    assert "Investment memo: not available" in output
    assert "Analysis: not available" in output


def test_record_disposition_completes_awaiting_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    repository = SqliteRunRepository(database)
    run = repository.create_run(
        memo_id="memo-disposition", as_of="2026-01-01T00:00:00Z"
    )
    for target in (
        WorkflowState.COLLECTING_EVIDENCE,
        WorkflowState.EVIDENCE_READY,
        WorkflowState.ANALYZING,
        WorkflowState.CHALLENGING,
        WorkflowState.SYNTHESIZING,
        WorkflowState.VALIDATING,
        WorkflowState.AWAITING_HUMAN_DISPOSITION,
    ):
        run = repository.transition(
            run.run_id, expected_state=run.state, target_state=target
        )

    assert (
        main(
            [
                "record-disposition",
                run.run_id,
                "watch",
                "--rationale",
                "Wait for evidence",
                "--database",
                str(database),
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "watch"
    assert output["state"] == "complete"


def test_import_prices_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "state.db"

    assert (
        main(
            [
                "import-prices",
                str(PRICE_FIXTURE),
                "--source",
                "Test fixture",
                "--database",
                str(database),
                "--artifact-root",
                str(tmp_path / "artifacts"),
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["row_count"] == 6
    assert output["start_date"] == "2025-01-02"


def test_analyze_portfolio_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "state.db"
    artifacts = tmp_path / "artifacts"
    assert (
        main(
            [
                "import-prices",
                str(PRICE_FIXTURE),
                "--source",
                "Test fixture",
                "--database",
                str(database),
                "--artifact-root",
                str(artifacts),
            ]
        )
        == 0
    )
    dataset = json.loads(capsys.readouterr().out)

    assert (
        main(
            [
                "analyze-portfolio",
                str(HOLDINGS_FIXTURE),
                "--dataset",
                dataset["dataset_id"],
                "--benchmark",
                "SPY",
                "--as-of",
                "2025-01-06",
                "--database",
                str(database),
                "--artifact-root",
                str(artifacts),
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["valuation_date"] == "2025-01-06"
    assert output["results"]["total_value"] == "199.50"


def test_backtest_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    database = tmp_path / "state.db"
    artifacts = tmp_path / "artifacts"
    assert (
        main(
            [
                "import-prices",
                str(BACKTEST_PRICE_FIXTURE),
                "--source",
                "Backtest fixture",
                "--database",
                str(database),
                "--artifact-root",
                str(artifacts),
            ]
        )
        == 0
    )
    dataset = json.loads(capsys.readouterr().out)

    assert (
        main(
            [
                "backtest",
                dataset["dataset_id"],
                "--ticker",
                "AAPL",
                "--benchmark",
                "SPY",
                "--short-window",
                "2",
                "--long-window",
                "3",
                "--transaction-cost-bps",
                "10",
                "--database",
                str(database),
                "--artifact-root",
                str(artifacts),
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["strategy_version"] == "1.0"
    assert output["results"]["trades"]
    assert all(
        trade["execution_date"] > trade["signal_date"]
        for trade in output["results"]["trades"]
    )
