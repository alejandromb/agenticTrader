"""Append-only persistence for human-owned research dispositions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import HumanDispositionEventModel

DispositionStatus = Literal["investigate", "watch", "reject", "consider_for_portfolio"]
ALLOWED_DISPOSITIONS = {
    "investigate",
    "watch",
    "reject",
    "consider_for_portfolio",
}


@dataclass(frozen=True, slots=True)
class HumanDispositionEvent:
    event_id: int
    run_id: str
    status: str
    rationale: str | None
    actor: str
    decided_at: str


class SqliteDispositionRepository:
    def __init__(self, database_path: Path) -> None:
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )

    def record(
        self,
        *,
        run_id: str,
        status: str,
        rationale: str | None = None,
        actor: str = "human_user",
    ) -> HumanDispositionEvent:
        if status not in ALLOWED_DISPOSITIONS:
            raise ValueError(f"Invalid human disposition: {status}")
        model = HumanDispositionEventModel(
            run_id=run_id,
            status=status,
            rationale=rationale.strip() if rationale and rationale.strip() else None,
            actor=actor,
            decided_at=datetime.now(UTC).isoformat(),
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _from_model(model)

    def for_run(self, run_id: str) -> HumanDispositionEvent | None:
        with self._sessions() as session:
            model = session.scalar(
                select(HumanDispositionEventModel).where(
                    HumanDispositionEventModel.run_id == run_id
                )
            )
            return _from_model(model) if model is not None else None


def _from_model(model: HumanDispositionEventModel) -> HumanDispositionEvent:
    return HumanDispositionEvent(
        event_id=model.event_id,
        run_id=model.run_id,
        status=model.status,
        rationale=model.rationale,
        actor=model.actor,
        decided_at=model.decided_at,
    )
