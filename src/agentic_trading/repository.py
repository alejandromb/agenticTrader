"""SQLAlchemy persistence for research runs and transition events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import Base, ResearchRunModel, TransitionEventModel
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
    """Persist workflow runs through SQLAlchemy using a local SQLite database."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._engine = create_sqlite_engine(database_path)
        self._sessions = sessionmaker(self._engine, expire_on_commit=False)

    def initialize(self) -> None:
        """Create tables for local bootstrap and tests.

        Deployed schema upgrades are managed by Alembic migrations.
        """
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        Base.metadata.create_all(self._engine)

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
        model = ResearchRunModel(
            run_id=identifier,
            memo_id=memo_id,
            workflow_version=workflow_version,
            state=WorkflowState.DRAFT,
            as_of=as_of,
            created_at=occurred_at,
            updated_at=occurred_at,
        )
        with self._sessions.begin() as session:
            session.add(model)
            session.add(
                TransitionEventModel(
                    run_id=identifier,
                    from_state=None,
                    to_state=WorkflowState.DRAFT,
                    occurred_at=occurred_at,
                    reason="run_created",
                )
            )
        return _run_from_model(model)

    def get_run(self, run_id: str) -> ResearchRun:
        """Return a run by ID."""
        with self._sessions() as session:
            model = session.get(ResearchRunModel, run_id)
            if model is None:
                raise RunNotFoundError(run_id)
            return _run_from_model(model)

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
        with self._sessions.begin() as session:
            result = session.execute(
                update(ResearchRunModel)
                .where(
                    ResearchRunModel.run_id == run_id,
                    ResearchRunModel.state == expected_state,
                )
                .values(state=target_state, updated_at=occurred_at)
            )
            if result.rowcount != 1:
                actual = session.scalar(
                    select(ResearchRunModel.state).where(
                        ResearchRunModel.run_id == run_id
                    )
                )
                if actual is None:
                    raise RunNotFoundError(run_id)
                raise ConcurrentTransitionError(
                    f"Expected {expected_state}, found {actual}"
                )
            session.add(
                TransitionEventModel(
                    run_id=run_id,
                    from_state=expected_state,
                    to_state=target_state,
                    occurred_at=occurred_at,
                    reason=reason,
                )
            )
        return self.get_run(run_id)

    def list_events(self, run_id: str) -> list[TransitionEvent]:
        """Return transition history in append order."""
        self.get_run(run_id)
        with self._sessions() as session:
            models = session.scalars(
                select(TransitionEventModel)
                .where(TransitionEventModel.run_id == run_id)
                .order_by(TransitionEventModel.event_id)
            ).all()
            return [_event_from_model(model) for model in models]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _run_from_model(model: ResearchRunModel) -> ResearchRun:
    return ResearchRun(
        run_id=model.run_id,
        memo_id=model.memo_id,
        workflow_version=model.workflow_version,
        state=WorkflowState(model.state),
        as_of=model.as_of,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _event_from_model(model: TransitionEventModel) -> TransitionEvent:
    return TransitionEvent(
        event_id=model.event_id,
        run_id=model.run_id,
        from_state=WorkflowState(model.from_state) if model.from_state else None,
        to_state=WorkflowState(model.to_state),
        occurred_at=model.occurred_at,
        reason=model.reason,
    )
