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
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)

    with pytest.raises(SystemExit, match="SEC_USER_AGENT is required"):
        main(["sec-filings", "320193", "--form", "10-K"])
