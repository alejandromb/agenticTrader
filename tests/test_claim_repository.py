from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from agentic_trading.claim_repository import SqliteClaimRepository
from agentic_trading.migrations import upgrade_database
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.source_repository import SqliteSourceRepository
from agentic_trading.xbrl import FilingFact


def fact() -> FilingFact:
    return FilingFact(
        taxonomy="us-gaap",
        concept="RevenueFromContractWithCustomerExcludingAssessedTax",
        label="Revenue",
        unit="USD",
        value=Decimal("416161000000"),
        period_start="2024-09-29",
        period_end="2025-09-27",
        filed="2025-10-31",
        form="10-K",
        accession_number="0000320193-25-000079",
        fiscal_year=2025,
        fiscal_period="FY",
    )


def create_run_and_source(database: Path, run_id: str, source_id: str) -> None:
    SqliteRunRepository(database).create_run(
        run_id=run_id,
        memo_id=f"memo-{run_id}",
        as_of="2025-10-31T23:59:59Z",
    )
    SqliteSourceRepository(database).register(
        source_id=source_id,
        run_id=run_id,
        source_type="regulatory_filing",
        title="Apple Inc. 2025 Form 10-K",
        publisher="SEC",
        canonical_url="https://www.sec.gov/example",
        source_identifier=f"SEC accession {source_id}",
        retrieved_at="2026-06-30T16:00:00Z",
        content_sha256=("a" if run_id == "run-001" else "b") * 64,
        size_bytes=100,
        storage_path=f"sha256/{source_id}",
    )


def test_candidate_fact_preserves_xbrl_and_source_lineage(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    create_run_and_source(database, "run-001", "source-001")
    claims = SqliteClaimRepository(database)

    claim = claims.register_xbrl_fact(
        claim_id="claim-001",
        run_id="run-001",
        source_id="source-001",
        fact=fact(),
    )

    assert claim.claim_type == "fact"
    assert claim.numeric_value == Decimal("416161000000")
    assert claim.source_id == "source-001"
    assert claim.extraction_method == "sec_companyfacts_v1"
    assert claims.list_for_run("run-001") == [claim]


def test_claim_cannot_reference_source_from_another_run(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    create_run_and_source(database, "run-001", "source-001")
    create_run_and_source(database, "run-002", "source-002")

    with pytest.raises(IntegrityError):
        SqliteClaimRepository(database).register_xbrl_fact(
            run_id="run-001",
            source_id="source-002",
            fact=fact(),
        )


def test_filing_statement_preserves_text_and_source_lineage(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    create_run_and_source(database, "run-001", "source-001")

    claim = SqliteClaimRepository(database).register_filing_statement(
        claim_id="claim-text-001",
        run_id="run-001",
        source_id="source-001",
        statement="Capital expenditures supported supply-chain automation.",
        topic="capital_allocation_purpose",
        period_end="2025-09-27",
        accession_number="0000320193-25-000079",
        sequence=1,
    )

    assert claim.claim_type == "filing_statement"
    assert claim.numeric_value is None
    assert claim.unit == "text"
    assert claim.extraction_method == "sec_filing_narrative_v1"
