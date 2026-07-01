import pytest
from sqlalchemy.exc import IntegrityError

from agentic_trading.disposition_repository import SqliteDispositionRepository
from agentic_trading.migrations import upgrade_database
from agentic_trading.repository import SqliteRunRepository


def test_human_disposition_is_append_only_and_separate(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    run = SqliteRunRepository(database).create_run(
        memo_id="memo-1", as_of="2026-01-01T00:00:00Z"
    )
    repository = SqliteDispositionRepository(database)

    event = repository.record(
        run_id=run.run_id,
        status="watch",
        rationale="Wait for stronger evidence.",
    )

    assert event.actor == "human_user"
    assert repository.for_run(run.run_id) == event
    with pytest.raises(IntegrityError):
        repository.record(run_id=run.run_id, status="reject")


def test_invalid_disposition_is_rejected(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)

    with pytest.raises(ValueError, match="Invalid human disposition"):
        SqliteDispositionRepository(database).record(run_id="missing", status="buy")
