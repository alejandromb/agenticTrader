from __future__ import annotations

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
from agentic_trading.migrations import upgrade_database
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.workflow import WorkflowState


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

    def fake_research(ticker: str, question: str):
        calls.append((ticker, question))
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
            {"ticker": "aapl", "question": "Assess the evidence"},
            token,
        )
        assert status == 201
        assert result["ticker"] == "AAPL"
        assert calls == [("AAPL", "Assess the evidence")]
