"""ORM persistence for evidence-linked candidate claims."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import CandidateClaimModel
from agentic_trading.xbrl import FilingFact


@dataclass(frozen=True, slots=True)
class CandidateClaim:
    claim_id: str
    run_id: str
    source_id: str
    claim_type: str
    statement: str
    taxonomy: str
    concept: str
    label: str
    unit: str
    numeric_value: Decimal
    period_start: str | None
    period_end: str
    accession_number: str
    extraction_method: str
    extracted_at: str


class SqliteClaimRepository:
    """Persist candidate claims through SQLAlchemy."""

    def __init__(self, database_path: Path) -> None:
        engine = create_sqlite_engine(database_path)
        self._sessions = sessionmaker(engine, expire_on_commit=False)

    def register_xbrl_fact(
        self,
        *,
        run_id: str,
        source_id: str,
        fact: FilingFact,
        statement: str | None = None,
        claim_id: str | None = None,
    ) -> CandidateClaim:
        """Register a deterministic XBRL observation as a candidate fact."""
        model = CandidateClaimModel(
            claim_id=claim_id or str(uuid4()),
            run_id=run_id,
            source_id=source_id,
            claim_type="fact",
            statement=statement or _default_statement(fact),
            taxonomy=fact.taxonomy,
            concept=fact.concept,
            label=fact.label,
            unit=fact.unit,
            numeric_value=str(fact.value),
            period_start=fact.period_start,
            period_end=fact.period_end,
            accession_number=fact.accession_number,
            extraction_method="sec_companyfacts_v1",
            extracted_at=datetime.now(UTC).isoformat(),
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _claim_from_model(model)

    def list_for_run(self, run_id: str) -> list[CandidateClaim]:
        """Return candidate claims in stable ID order."""
        with self._sessions() as session:
            models = session.scalars(
                select(CandidateClaimModel)
                .where(CandidateClaimModel.run_id == run_id)
                .order_by(CandidateClaimModel.claim_id)
            ).all()
            return [_claim_from_model(model) for model in models]


def _default_statement(fact: FilingFact) -> str:
    return (
        f"{fact.label} was {fact.value} {fact.unit} "
        f"for the period ended {fact.period_end}."
    )


def _claim_from_model(model: CandidateClaimModel) -> CandidateClaim:
    return CandidateClaim(
        claim_id=model.claim_id,
        run_id=model.run_id,
        source_id=model.source_id,
        claim_type=model.claim_type,
        statement=model.statement,
        taxonomy=model.taxonomy,
        concept=model.concept,
        label=model.label,
        unit=model.unit,
        numeric_value=Decimal(model.numeric_value),
        period_start=model.period_start,
        period_end=model.period_end,
        accession_number=model.accession_number,
        extraction_method=model.extraction_method,
        extracted_at=model.extracted_at,
    )
