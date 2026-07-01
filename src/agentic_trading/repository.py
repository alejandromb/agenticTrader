"""SQLite persistence for research runs and append-only transition events."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from agentic_trading.workflow import WorkflowState, can_transition


class RunNotFoundError(LookupError):
    """Raised when a research run does not exist."""


class InvalidTransitionError(ValueError):
    """Raised when a workflow transition is not allowed."""


class ConcurrentTransitionError(RuntimeError):
    """Raised when persisted state differs from the caller's expectation."""


@dataclass(frozen=True, slots=True)
class ResearchRun:
    run_id: str
    memo_id: str
    workflow_version: str
    state: WorkflowState
    as_of: str
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class TransitionEvent:
    event_id: int
    run_id: str
    from_state: WorkflowState | None
    to_state: WorkflowState
    occurred_at: str
    reason: str | None


class SqliteRunRepository:
    """Persist workflow runs in a local SQLite database."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        """Create repository tables when they do not exist."""
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS research_runs (
                    run_id TEXT PRIMARY KEY,
                    memo_id TEXT NOT NULL UNIQUE,
                    workflow_version TEXT NOT NULL,
                    state TEXT NOT NULL,
                    as_of TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transition_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL REFERENCES research_runs(run_id),
                    from_state TEXT,
                    to_state TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    reason TEXT
                );

                CREATE INDEX IF NOT EXISTS transition_events_run_id
                    ON transition_events(run_id, event_id);
                """
            )

    def create_run(
        self,
        *,
        memo_id: str,
        as_of: str,
        workflow_version: str = "1.0.0",
        run_id: str | None = None,
    ) -> ResearchRun:
        """Create a draft run and its initial append-only event."""
        identifier = run_id or str(uuid4())
        occurred_at = _utc_now()
        with self._transaction() as connection:
            connection.execute(
                """
                INSERT INTO research_runs (
                    run_id, memo_id, workflow_version, state, as_of,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    identifier,
                    memo_id,
                    workflow_version,
                    WorkflowState.DRAFT,
                    as_of,
                    occurred_at,
                    occurred_at,
                ),
            )
            connection.execute(
                """
                INSERT INTO transition_events (
                    run_id, from_state, to_state, occurred_at, reason
                ) VALUES (?, NULL, ?, ?, ?)
                """,
                (identifier, WorkflowState.DRAFT, occurred_at, "run_created"),
            )
        return self.get_run(identifier)

    def get_run(self, run_id: str) -> ResearchRun:
        """Return a run by ID."""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM research_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
        if row is None:
            raise RunNotFoundError(run_id)
        return _run_from_row(row)

    def transition(
        self,
        run_id: str,
        *,
        expected_state: WorkflowState,
        target_state: WorkflowState,
        reason: str | None = None,
    ) -> ResearchRun:
        """Atomically transition a run and append an event."""
        if not can_transition(expected_state, target_state):
            raise InvalidTransitionError(
                f"Cannot transition {expected_state} -> {target_state}"
            )

        occurred_at = _utc_now()
        with self._transaction() as connection:
            cursor = connection.execute(
                """
                UPDATE research_runs
                SET state = ?, updated_at = ?
                WHERE run_id = ? AND state = ?
                """,
                (target_state, occurred_at, run_id, expected_state),
            )
            if cursor.rowcount != 1:
                actual = connection.execute(
                    "SELECT state FROM research_runs WHERE run_id = ?", (run_id,)
                ).fetchone()
                if actual is None:
                    raise RunNotFoundError(run_id)
                raise ConcurrentTransitionError(
                    f"Expected {expected_state}, found {actual['state']}"
                )
            connection.execute(
                """
                INSERT INTO transition_events (
                    run_id, from_state, to_state, occurred_at, reason
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, expected_state, target_state, occurred_at, reason),
            )
        return self.get_run(run_id)

    def list_events(self, run_id: str) -> list[TransitionEvent]:
        """Return transition history in append order."""
        self.get_run(run_id)
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM transition_events
                WHERE run_id = ? ORDER BY event_id
                """,
                (run_id,),
            ).fetchall()
        return [_event_from_row(row) for row in rows]

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise
            else:
                connection.commit()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _run_from_row(row: sqlite3.Row) -> ResearchRun:
    return ResearchRun(
        run_id=row["run_id"],
        memo_id=row["memo_id"],
        workflow_version=row["workflow_version"],
        state=WorkflowState(row["state"]),
        as_of=row["as_of"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _event_from_row(row: sqlite3.Row) -> TransitionEvent:
    from_state = row["from_state"]
    return TransitionEvent(
        event_id=row["event_id"],
        run_id=row["run_id"],
        from_state=WorkflowState(from_state) if from_state else None,
        to_state=WorkflowState(row["to_state"]),
        occurred_at=row["occurred_at"],
        reason=row["reason"],
    )
