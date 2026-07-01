from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_trading.cli import main

ROOT = Path(__file__).parents[1]


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
    assert "Analysis: not available" in output
