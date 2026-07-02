from __future__ import annotations

import base64
import json
import threading
from contextlib import contextmanager
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from agentic_trading.dashboard import (
    DashboardDataService,
    DashboardError,
    create_dashboard_server,
)
from agentic_trading.dashboard_workspace import DashboardWorkspaceService
from agentic_trading.migrations import upgrade_database
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.workflow import WorkflowState

FIXTURES = Path(__file__).parent / "fixtures"


def awaiting_run(database: Path) -> str:
    upgrade_database(database)
    repository = SqliteRunRepository(database)
    run = repository.create_run(memo_id="memo-dashboard", as_of="2026-01-01T00:00:00Z")
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
    return run.run_id


@contextmanager
def running_dashboard(tmp_path, monkeypatch):
    database = tmp_path / "state.db"
    run_id = awaiting_run(database)
    monkeypatch.setenv("OPENAI_API_KEY", "private-openai-secret")
    monkeypatch.setenv("SEC_USER_AGENT", "private-sec-identity")
    calls = []

    def fake_research(ticker: str, question: str, form: str):
        calls.append((ticker, question, form))
        return {
            "run_id": "new-run",
            "state": "awaiting_human_disposition",
            "ticker": ticker,
            "company": "Fixture Company",
            "memo_artifact_id": "memo-new",
        }

    server = create_dashboard_server(
        host="127.0.0.1",
        port=0,
        database_path=database,
        artifact_root=tmp_path / "artifacts",
        research_runner=fake_research,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", database, run_id, calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def get_json(url: str):
    with urlopen(url) as response:  # noqa: S310
        return response.status, json.load(response), response.headers


def post_json(url: str, payload: dict, token: str | None = None):
    headers = {"Content-Type": "application/json"}
    if token is not None:
        headers["X-Agentic-CSRF"] = token
    request = Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST",
    )
    with urlopen(request) as response:  # noqa: S310
        return response.status, json.load(response)


def error_json(error: HTTPError) -> dict:
    with error:
        return json.load(error)


def test_server_rejects_non_loopback_binding(tmp_path) -> None:
    with pytest.raises(DashboardError, match="loopback"):
        create_dashboard_server(
            host="0.0.0.0",
            port=0,
            database_path=tmp_path / "state.db",
            artifact_root=tmp_path / "artifacts",
        )


def test_dashboard_assets_and_configuration_are_secret_safe(
    tmp_path, monkeypatch
) -> None:
    with running_dashboard(tmp_path, monkeypatch) as (base, _, _, _):
        with urlopen(base) as response:  # noqa: S310
            page = response.read().decode()
            assert response.status == 200
            assert "Agentic Trading" in page
            assert "default-src 'self'" in response.headers["Content-Security-Policy"]

        status, config, headers = get_json(f"{base}/api/config")
        assert status == 200
        assert config["openai_configured"] is True
        assert config["sec_configured"] is True
        assert len(config["csrf_token"]) >= 32
        assert "private-openai-secret" not in json.dumps(config)
        assert "private-sec-identity" not in json.dumps(config)
        assert headers["Cache-Control"] == "no-store"
        _, workspace, _ = get_json(f"{base}/api/workspace")
        assert workspace["quality_evaluations"] == []


def test_run_list_detail_and_disposition_lifecycle(tmp_path, monkeypatch) -> None:
    with running_dashboard(tmp_path, monkeypatch) as (base, database, run_id, _):
        _, config, _ = get_json(f"{base}/api/config")
        _, runs, _ = get_json(f"{base}/api/runs")
        assert [item["run_id"] for item in runs["runs"]] == [run_id]

        _, detail, _ = get_json(f"{base}/api/runs/{run_id}")
        assert detail["run"]["state"] == "awaiting_human_disposition"
        assert detail["can_record_disposition"] is True
        assert detail["memo"] is None

        with pytest.raises(HTTPError) as rejected:
            post_json(
                f"{base}/api/runs/{run_id}/disposition",
                {"status": "watch", "rationale": "Human review"},
            )
        assert rejected.value.code == 403
        assert error_json(rejected.value)["error"] == "Invalid request token"

        status, recorded = post_json(
            f"{base}/api/runs/{run_id}/disposition",
            {"status": "watch", "rationale": "Human review"},
            config["csrf_token"],
        )
        assert status == 201
        assert recorded["state"] == "complete"
        persisted = DashboardDataService(database).run_detail(run_id)
        assert persisted["disposition"]["status"] == "watch"
        assert persisted["can_record_disposition"] is False


def test_research_endpoint_validates_and_uses_existing_service_boundary(
    tmp_path, monkeypatch
) -> None:
    with running_dashboard(tmp_path, monkeypatch) as (base, _, _, calls):
        _, config, _ = get_json(f"{base}/api/config")
        token = config["csrf_token"]
        with pytest.raises(HTTPError) as rejected:
            post_json(
                f"{base}/api/research",
                {"ticker": "bad ticker", "question": "Assess it"},
                token,
            )
        assert rejected.value.code == 400
        assert "Ticker format" in error_json(rejected.value)["error"]

        status, result = post_json(
            f"{base}/api/research",
            {"ticker": "aapl", "question": "Assess the evidence", "form": "10-Q"},
            token,
        )
        assert status == 201
        assert result["ticker"] == "AAPL"
        assert calls == [("AAPL", "Assess the evidence", "10-Q")]


def test_quantitative_monitoring_and_alert_http_workflow(tmp_path, monkeypatch) -> None:
    with running_dashboard(tmp_path, monkeypatch) as (base, _, run_id, _):
        _, config, _ = get_json(f"{base}/api/config")
        token = config["csrf_token"]
        price_bytes = (FIXTURES / "prices-backtest.csv").read_bytes()
        status, dataset = post_json(
            f"{base}/api/prices/import",
            {
                "content_base64": base64.b64encode(price_bytes).decode(),
                "source": "Dashboard fixture",
                "adjustment_note": "Fixture adjusted closes",
            },
            token,
        )
        assert status == 201
        assert Path(dataset["storage_path"]).read_bytes() == price_bytes

        _, snapshot, _ = get_json(f"{base}/api/workspace")
        assert [item["dataset_id"] for item in snapshot["datasets"]] == [
            dataset["dataset_id"]
        ]

        status, screen = post_json(
            f"{base}/api/screens",
            {"as_of": "2027-01-01T00:00:00Z"},
            token,
        )
        assert status == 201
        assert screen["screen_id"]
        assert screen["results"] == []

        holdings = b"ticker,shares\nAAPL,2\n"
        status, portfolio = post_json(
            f"{base}/api/portfolio",
            {
                "content_base64": base64.b64encode(holdings).decode(),
                "dataset_id": dataset["dataset_id"],
                "benchmark": "SPY",
                "as_of": "2025-01-15",
            },
            token,
        )
        assert status == 201
        assert portfolio["results"]["total_value"] == "18"

        status, backtest = post_json(
            f"{base}/api/backtests",
            {
                "dataset_id": dataset["dataset_id"],
                "ticker": "AAPL",
                "benchmark": "SPY",
                "short_window": 2,
                "long_window": 3,
                "initial_cash": "10000",
                "transaction_cost_bps": "10",
            },
            token,
        )
        assert status == 201
        assert backtest["strategy_version"] == "1.0"
        assert backtest["results"]["trades"]

        post_json(
            f"{base}/api/runs/{run_id}/disposition",
            {"status": "watch", "rationale": "Eligible monitoring fixture"},
            token,
        )
        status, monitor = post_json(
            f"{base}/api/monitors",
            {
                "run_id": run_id,
                "name": "Dashboard monitor",
                "rules": [
                    {
                        "rule_id": "price-floor",
                        "type": "price_below",
                        "ticker": "AAPL",
                        "threshold": "10",
                    }
                ],
            },
            token,
        )
        assert status == 201
        status, evaluation = post_json(
            f"{base}/api/monitors/{monitor['monitor_id']}/evaluate",
            {"dataset_id": dataset["dataset_id"], "as_of": "2025-01-15"},
            token,
        )
        assert status == 201
        assert evaluation["results"][0]["triggered"] is True

        _, snapshot, _ = get_json(f"{base}/api/workspace")
        alert = snapshot["alerts"][0]
        assert alert["status"] == "open"
        status, acknowledgement = post_json(
            f"{base}/api/alerts/{alert['alert_id']}/acknowledge",
            {"note": "Reviewed in dashboard"},
            token,
        )
        assert status == 201
        assert acknowledgement["alert_id"] == alert["alert_id"]


def test_uploaded_file_requires_strict_base64(tmp_path, monkeypatch) -> None:
    with running_dashboard(tmp_path, monkeypatch) as (base, _, _, _):
        _, config, _ = get_json(f"{base}/api/config")
        with pytest.raises(HTTPError) as rejected:
            post_json(
                f"{base}/api/prices/import",
                {
                    "content_base64": "not base64!",
                    "source": "Invalid",
                    "adjustment_note": "Invalid",
                },
                config["csrf_token"],
            )
        assert rejected.value.code == 400
        assert "valid base64" in error_json(rejected.value)["error"]

        with pytest.raises(HTTPError) as invalid_filter:
            post_json(
                f"{base}/api/screens",
                {
                    "as_of": "2027-01-01T00:00:00Z",
                    "min_revenue_growth": [],
                },
                config["csrf_token"],
            )
        assert invalid_filter.value.code == 400
        assert "decimal" in error_json(invalid_filter.value)["error"]


def test_quality_evaluation_endpoint_preserves_human_score_payload(
    tmp_path, monkeypatch
) -> None:
    captured = {}

    def fake_evaluate(self, *, run_id, scores):
        captured.update({"run_id": run_id, "scores": scores})
        return {"evaluation_id": "quality-1", "accepted": True, "total_score": 12}

    monkeypatch.setattr(
        DashboardWorkspaceService,
        "evaluate_research_quality",
        fake_evaluate,
    )
    with running_dashboard(tmp_path, monkeypatch) as (base, _, run_id, _):
        _, config, _ = get_json(f"{base}/api/config")
        score_payload = {
            criterion: {"score": 2, "rationale": f"Reviewed {criterion}"}
            for criterion in (
                "numerical_fidelity",
                "evidence_fidelity",
                "fact_judgment_separation",
                "balance",
                "uncertainty",
                "decision_usefulness",
            )
        }

        status, result = post_json(
            f"{base}/api/quality-evaluations",
            {"run_id": run_id, "scores": score_payload},
            config["csrf_token"],
        )

        assert status == 201
        assert result["evaluation_id"] == "quality-1"
        assert captured == {"run_id": run_id, "scores": score_payload}
