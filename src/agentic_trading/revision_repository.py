"""Persistence for visible cross-filing revision audits."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import RevisionAuditModel
from agentic_trading.xbrl import CrossFilingRevision


@dataclass(frozen=True, slots=True)
class RevisionAudit:
    audit_id: str
    run_id: str
    revision: CrossFilingRevision
    created_at: str


class SqliteRevisionAuditRepository:
    def __init__(self, database_path: Path) -> None:
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )

    def register(self, run_id: str, revision: CrossFilingRevision) -> RevisionAudit:
        model = RevisionAuditModel(
            audit_id=str(uuid4()),
            run_id=run_id,
            classification=revision.classification,
            concept=revision.concept,
            unit=revision.unit,
            period_start=revision.period_start,
            period_end=revision.period_end,
            original_accession=revision.original_accession,
            original_value=str(revision.original_value),
            later_accession=revision.later_accession,
            later_value=str(revision.later_value),
            absolute_change=str(revision.absolute_change),
            created_at=datetime.now(UTC).isoformat(),
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _from_model(model)

    def list_for_run(self, run_id: str) -> list[RevisionAudit]:
        with self._sessions() as session:
            models = session.scalars(
                select(RevisionAuditModel).where(RevisionAuditModel.run_id == run_id)
            ).all()
            return [_from_model(model) for model in models]


def _from_model(model: RevisionAuditModel) -> RevisionAudit:
    revision = CrossFilingRevision(
        concept=model.concept,
        unit=model.unit,
        period_start=model.period_start,
        period_end=model.period_end,
        original_accession=model.original_accession,
        original_value=Decimal(model.original_value),
        later_accession=model.later_accession,
        later_value=Decimal(model.later_value),
        absolute_change=Decimal(model.absolute_change),
        classification=model.classification,
    )
    return RevisionAudit(model.audit_id, model.run_id, revision, model.created_at)
