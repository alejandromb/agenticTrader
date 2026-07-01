from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from agentic_trading.analysis import AnalysisPoint, FinancialAnalysis
from agentic_trading.analysis_repository import SqliteAnalysisRepository
from agentic_trading.claim_repository import SqliteClaimRepository
from agentic_trading.migrations import upgrade_database
from agentic_trading.openai_adapter import GeneratedFinancialAnalysis
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.source_repository import SqliteSourceRepository
from agentic_trading.xbrl import FilingFact


def create_claim(database: Path, suffix: str) -> str:
    run_id = f"run-{suffix}"
    source_id = f"source-{suffix}"
    claim_id = f"claim-{suffix}"
    SqliteRunRepository(database).create_run(
        run_id=run_id,
        memo_id=f"memo-{suffix}",
        as_of="2025-10-31T23:59:59Z",
    )
    SqliteSourceRepository(database).register(
        source_id=source_id,
        run_id=run_id,
        source_type="regulatory_filing",
        title="Apple Inc. 2025 Form 10-K",
        publisher="SEC",
        canonical_url=f"https://www.sec.gov/{suffix}",
        source_identifier=f"SEC accession {suffix}",
        retrieved_at="2026-07-01T00:00:00Z",
        content_sha256=suffix * 64,
        size_bytes=100,
        storage_path=f"sha256/{suffix}",
    )
    SqliteClaimRepository(database).register_xbrl_fact(
        claim_id=claim_id,
        run_id=run_id,
        source_id=source_id,
        fact=FilingFact(
            taxonomy="us-gaap",
            concept="RevenueFromContractWithCustomerExcludingAssessedTax",
            label="Revenue",
            unit="USD",
            value=Decimal("416161000000"),
            period_start="2024-09-29",
            period_end="2025-09-27",
            filed="2025-10-31",
            form="10-K",
            accession_number=f"accession-{suffix}",
            fiscal_year=2025,
            fiscal_period="FY",
        ),
    )
    return claim_id


def generated(
    claim_id: str, response_id: str = "response-001"
) -> GeneratedFinancialAnalysis:
    return GeneratedFinancialAnalysis(
        analysis=FinancialAnalysis(
            assessment="positive",
            summary="Revenue scale is a strength.",
            strengths=[AnalysisPoint(text="Large revenue base.", claim_ids=[claim_id])],
            concerns=[],
            uncertainties=[],
        ),
        model="test-model",
        provider_response_id=response_id,
        prompt_version="1.0.0",
        input_claim_ids=(claim_id,),
        evidence_gaps=("Missing liabilities",),
    )


def test_analysis_artifact_preserves_model_and_claim_lineage(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    claim_id = create_claim(database, "a")

    artifact = SqliteAnalysisRepository(database).save_openai_financial_analysis(
        artifact_id="analysis-001",
        run_id="run-a",
        generated=generated(claim_id),
    )

    assert artifact.model == "test-model"
    assert artifact.provider == "openai"
    assert artifact.input_claim_ids == (claim_id,)
    assert artifact.evidence_gaps == ("Missing liabilities",)
    assert artifact.analysis.assessment == "positive"
    assert SqliteAnalysisRepository(database).latest_for_run("run-a") == artifact


def test_analysis_cannot_link_claim_from_another_run(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    create_claim(database, "a")
    other_claim = create_claim(database, "b")

    with pytest.raises(IntegrityError):
        SqliteAnalysisRepository(database).save_openai_financial_analysis(
            run_id="run-a",
            generated=generated(other_claim),
        )
