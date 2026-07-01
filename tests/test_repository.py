from __future__ import annotations

from pathlib import Path

import pytest

from agentic_trading.repository import (
    ConcurrentTransitionError,
    InvalidTransitionError,
    RunNotFoundError,
    SqliteRunRepository,
)
from agentic_trading.workflow import WorkflowState


@pytest.fixture
def repository(tmp_path: Path) -> SqliteRunRepository:
    value = SqliteRunRepository(tmp_path / "state" / "agentic-trading.db")
    value.initialize()
    return value


def test_create_run_records_initial_event(repository: SqliteRunRepository) -> None:
    run = repository.create_run(
        run_id="run-001",
        memo_id="memo-001",
        as_of="2025-10-31T23:59:59Z",
    )

    assert run.state is WorkflowState.DRAFT
    events = repository.list_events(run.run_id)
    assert len(events) == 1
    assert events[0].from_state is None
    assert events[0].to_state is WorkflowState.DRAFT


def test_valid_transition_updates_run_and_appends_event(
    repository: SqliteRunRepository,
) -> None:
    run = repository.create_run(
        run_id="run-001",
        memo_id="memo-001",
        as_of="2025-10-31T23:59:59Z",
    )

    updated = repository.transition(
        run.run_id,
        expected_state=WorkflowState.DRAFT,
        target_state=WorkflowState.COLLECTING_EVIDENCE,
        reason="collection_started",
    )

    assert updated.state is WorkflowState.COLLECTING_EVIDENCE
    events = repository.list_events(run.run_id)
    assert [event.to_state for event in events] == [
        WorkflowState.DRAFT,
        WorkflowState.COLLECTING_EVIDENCE,
    ]


def test_invalid_transition_does_not_change_state(
    repository: SqliteRunRepository,
) -> None:
    run = repository.create_run(
        run_id="run-001",
        memo_id="memo-001",
        as_of="2025-10-31T23:59:59Z",
    )

    with pytest.raises(InvalidTransitionError):
        repository.transition(
            run.run_id,
            expected_state=WorkflowState.DRAFT,
            target_state=WorkflowState.ANALYZING,
        )

    assert repository.get_run(run.run_id).state is WorkflowState.DRAFT


def test_stale_expected_state_is_rejected(repository: SqliteRunRepository) -> None:
    run = repository.create_run(
        run_id="run-001",
        memo_id="memo-001",
        as_of="2025-10-31T23:59:59Z",
    )
    repository.transition(
        run.run_id,
        expected_state=WorkflowState.DRAFT,
        target_state=WorkflowState.COLLECTING_EVIDENCE,
    )

    with pytest.raises(ConcurrentTransitionError, match="found collecting_evidence"):
        repository.transition(
            run.run_id,
            expected_state=WorkflowState.DRAFT,
            target_state=WorkflowState.COLLECTING_EVIDENCE,
        )


def test_unknown_run_is_rejected(repository: SqliteRunRepository) -> None:
    with pytest.raises(RunNotFoundError):
        repository.get_run("missing")


def test_active_run_can_fail(repository: SqliteRunRepository) -> None:
    run = repository.create_run(
        run_id="run-001",
        memo_id="memo-001",
        as_of="2025-10-31T23:59:59Z",
    )

    failed = repository.transition(
        run.run_id,
        expected_state=WorkflowState.DRAFT,
        target_state=WorkflowState.FAILED,
        reason="cancelled",
    )

    assert failed.state is WorkflowState.FAILED


def test_list_runs_returns_persisted_runs(repository: SqliteRunRepository) -> None:
    run = repository.create_run(
        run_id="run-001",
        memo_id="memo-001",
        as_of="2025-10-31T23:59:59Z",
    )

    assert repository.list_runs() == [run]
