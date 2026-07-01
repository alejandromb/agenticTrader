import json
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from agentic_trading.calculations import DerivedCalculation
from agentic_trading.claim_repository import SqliteClaimRepository
from agentic_trading.database import create_sqlite_engine
from agentic_trading.migrations import upgrade_database
from agentic_trading.models import AnalysisArtifactModel, InvestmentMemoArtifactModel
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.screener import ScreenFilters, SqliteResearchScreener
from agentic_trading.source_repository import SqliteSourceRepository
from agentic_trading.xbrl import FilingFact


def add_research_record(database, *, ticker: str, as_of: str, growth: str) -> str:
    run = SqliteRunRepository(database).create_run(
        memo_id=f"memo-{ticker}-{growth}", as_of=as_of
    )
    source = SqliteSourceRepository(database).register(
        run_id=run.run_id,
        source_type="regulatory_filing",
        title=f"{ticker} filing",
        publisher="SEC",
        canonical_url=f"https://www.sec.gov/{ticker}",
        source_identifier=f"accession-{ticker}-{growth}",
        retrieved_at=as_of,
        content_sha256=("a" if ticker == "AAA" else "b") * 64,
        size_bytes=1,
        storage_path=f"artifact-{ticker}",
    )
    fact = FilingFact(
        taxonomy="us-gaap",
        concept="Revenue",
        label="Revenue",
        unit="USD",
        value=Decimal("100"),
        period_start="2024-01-01",
        period_end="2024-12-31",
        filed="2025-01-01",
        form="10-K",
        accession_number=f"accession-{ticker}",
        fiscal_year=2024,
        fiscal_period="FY",
    )
    claims = SqliteClaimRepository(database)
    input_claim = claims.register_xbrl_fact(
        run_id=run.run_id, source_id=source.source_id, fact=fact
    )
    claims.register_calculation(
        run_id=run.run_id,
        source_id=source.source_id,
        calculation=DerivedCalculation(
            concept="revenue_growth",
            label="Revenue growth",
            formula="test formula",
            value=Decimal(growth),
            unit="percent",
            period_start="2024-01-01",
            period_end="2024-12-31",
            accession_number=fact.accession_number,
            input_facts=(fact,),
        ),
        input_claim_ids=(input_claim.claim_id,),
    )
    now = datetime.now(UTC).isoformat()
    with Session(create_sqlite_engine(database)) as session, session.begin():
        analysis = AnalysisArtifactModel(
            artifact_id=f"analysis-{ticker}-{growth}",
            run_id=run.run_id,
            artifact_type="financial_analysis",
            schema_version="1",
            provider="test",
            model="test",
            provider_response_id=f"response-{ticker}-{growth}",
            prompt_version="test",
            evidence_gaps_json="[]",
            content_json="{}",
            created_at=now,
        )
        session.add(analysis)
        session.flush()
        session.add(
            InvestmentMemoArtifactModel(
                artifact_id=f"memo-artifact-{ticker}-{growth}",
                run_id=run.run_id,
                analysis_artifact_id=analysis.artifact_id,
                schema_version="2.0.0",
                content_json=json.dumps({"subject": {"ticker": ticker}}),
                created_at=now,
            )
        )
    return run.run_id


def test_screen_respects_as_of_filters_and_persists_results(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    included_run = add_research_record(
        database, ticker="AAA", as_of="2025-01-02T00:00:00Z", growth="6"
    )
    add_research_record(
        database, ticker="BBB", as_of="2026-01-02T00:00:00Z", growth="10"
    )
    screener = SqliteResearchScreener(database)

    artifact = screener.screen(
        as_of="2025-12-31T23:59:59Z",
        filters=ScreenFilters(min_revenue_growth=Decimal("5")),
    )

    assert [(item.ticker, item.run_id) for item in artifact.results] == [
        ("AAA", included_run)
    ]
    assert screener.get(artifact.screen_id) == artifact


def test_screen_excludes_missing_required_metric(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    add_research_record(
        database, ticker="AAA", as_of="2025-01-02T00:00:00Z", growth="6"
    )

    artifact = SqliteResearchScreener(database).screen(
        as_of="2025-12-31T23:59:59Z",
        filters=ScreenFilters(min_current_ratio=Decimal("1")),
    )

    assert artifact.results == ()
