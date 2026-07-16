from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from agentic_trading.cli import main
from agentic_trading.disposition_repository import SqliteDispositionRepository
from agentic_trading.market_data import PriceDataset
from agentic_trading.migrations import upgrade_database
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.research_quality import (
    CriterionScore,
    ResearchQualityEvaluation,
)
from agentic_trading.workflow import WorkflowState

ROOT = Path(__file__).parents[1]
PRICE_FIXTURE = ROOT / "tests/fixtures/prices-valid.csv"
BACKTEST_PRICE_FIXTURE = ROOT / "tests/fixtures/prices-backtest.csv"
HOLDINGS_FIXTURE = ROOT / "tests/fixtures/holdings-valid.csv"
MONITOR_RULES_FIXTURE = ROOT / "tests/fixtures/monitor-rules.json"


def create_completed_watch_run(database: Path) -> str:
    upgrade_database(database)
    repository = SqliteRunRepository(database)
    run = repository.create_run(
        memo_id="memo-cli-monitor", as_of="2025-01-01T00:00:00Z"
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
    SqliteDispositionRepository(database).record(
        run_id=run.run_id, status="watch", rationale="CLI fixture"
    )
    repository.transition(
        run.run_id,
        expected_state=run.state,
        target_state=WorkflowState.COMPLETE,
    )
    return run.run_id


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
    monkeypatch.setenv("ALPACA_API_KEY", "private-alpaca-value")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "private-alpaca-secret")

    assert main(["doctor", "--database", str(database)]) == 0

    output = capsys.readouterr().out
    assert "private-openai-value" not in output
    assert "private-sec-value" not in output
    assert "private-alpaca-value" not in output
    assert "private-alpaca-secret" not in output
    assert json.loads(output) == {
        "alpaca_market_data_configured": True,
        "database_exists": True,
        "market_data_configured": True,
        "market_data_provider": "alpaca",
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


def test_research_quality_cli_creates_and_lists_evaluations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    score_path = tmp_path / "scores.json"
    score_path.write_text(
        json.dumps(
            {
                criterion: {"score": 2, "rationale": "Reviewed"}
                for criterion in (
                    "numerical_fidelity",
                    "evidence_fidelity",
                    "fact_judgment_separation",
                    "balance",
                    "uncertainty",
                    "decision_usefulness",
                )
            }
        )
    )
    evaluation = ResearchQualityEvaluation(
        evaluation_id="quality-cli",
        run_id="run-cli",
        analysis_artifact_id="analysis-cli",
        memo_artifact_id="memo-cli",
        rubric_version="1.0.0",
        gates={"artifacts_present": True},
        scores={
            "balance": CriterionScore(score=2, rationale="Reviewed")
        },
        total_score=12,
        accepted=True,
        provenance={"prompt_version": "2.2.0"},
        actor="human_user",
        created_at="2026-07-02T00:00:00Z",
    )

    class FakeRepository:
        def __init__(self, database):
            self.database = database

        def evaluate(self, run_id, *, scores):
            assert run_id == "run-cli"
            assert scores["balance"]["score"] == 2
            return evaluation

        def list_evaluations(self, *, run_id=None):
            assert run_id == "run-cli"
            return (evaluation,)

    monkeypatch.setattr(
        "agentic_trading.cli.SqliteResearchQualityRepository", FakeRepository
    )
    database = tmp_path / "state.db"

    assert (
        main(
            [
                "evaluate-research-quality",
                "run-cli",
                "--scores",
                str(score_path),
                "--database",
                str(database),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out) == asdict(evaluation)

    assert (
        main(
            [
                "list-research-evaluations",
                "--run-id",
                "run-cli",
                "--database",
                str(database),
            ]
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out) == [asdict(evaluation)]


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


def test_fetch_prices_command_is_read_only_and_secret_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    captured = {}
    dataset = PriceDataset(
        dataset_id="alpaca-dataset",
        source="Alpaca Market Data v2; feed=iex",
        retrieved_at="2026-07-02T00:00:00Z",
        content_sha256="a" * 64,
        storage_path="artifacts/alpaca",
        adjustment_note="adjustment=all",
        row_count=4,
        start_date="2026-01-01",
        end_date="2026-01-02",
        created_at="2026-07-02T00:00:00Z",
    )

    def fake_fetch(database, artifact_root, **kwargs):
        captured.update(kwargs)
        return dataset

    monkeypatch.setenv("ALPACA_API_KEY", "private-key")
    monkeypatch.setenv("ALPACA_SECRET_KEY", "private-secret")
    monkeypatch.setattr("agentic_trading.cli.fetch_and_store_alpaca_prices", fake_fetch)

    assert (
        main(
            [
                "fetch-prices",
                "AAPL",
                "SPY",
                "--start",
                "2026-01-01",
                "--end",
                "2026-01-02",
                "--database",
                str(tmp_path / "state.db"),
                "--artifact-root",
                str(tmp_path / "artifacts"),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert json.loads(output)["dataset_id"] == "alpaca-dataset"
    assert "private-key" not in output
    assert "private-secret" not in output
    assert captured["symbols"] == ["AAPL", "SPY"]
    assert captured["feed"] == "iex"


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


def test_monitor_evaluate_list_and_acknowledge_commands(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    database = tmp_path / "state.db"
    artifacts = tmp_path / "artifacts"
    run_id = create_completed_watch_run(database)
    assert (
        main(
            [
                "import-prices",
                str(PRICE_FIXTURE),
                "--source",
                "Monitoring fixture",
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
                "create-monitor",
                run_id,
                "--name",
                "CLI monitor",
                "--rules",
                str(MONITOR_RULES_FIXTURE),
                "--database",
                str(database),
                "--artifact-root",
                str(artifacts),
            ]
        )
        == 0
    )
    monitor = json.loads(capsys.readouterr().out)

    evaluation_args = [
        "evaluate-monitor",
        monitor["monitor_id"],
        "--dataset",
        dataset["dataset_id"],
        "--as-of",
        "2025-01-06",
        "--database",
        str(database),
        "--artifact-root",
        str(artifacts),
    ]
    assert main(evaluation_args) == 0
    evaluation = json.loads(capsys.readouterr().out)
    assert main(evaluation_args) == 0
    assert json.loads(capsys.readouterr().out) == evaluation

    assert (
        main(
            [
                "list-alerts",
                "--monitor",
                monitor["monitor_id"],
                "--status",
                "open",
                "--database",
                str(database),
                "--artifact-root",
                str(artifacts),
            ]
        )
        == 0
    )
    alerts = json.loads(capsys.readouterr().out)
    assert len(alerts) == 2

    assert (
        main(
            [
                "acknowledge-alert",
                alerts[0]["alert_id"],
                "--note",
                "Reviewed",
                "--database",
                str(database),
                "--artifact-root",
                str(artifacts),
            ]
        )
        == 0
    )
    acknowledgement = json.loads(capsys.readouterr().out)
    assert acknowledgement["alert_id"] == alerts[0]["alert_id"]
