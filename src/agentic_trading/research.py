"""User-facing orchestration for one-company research runs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from agentic_trading.analysis_repository import (
    AnalysisArtifact,
    SqliteAnalysisRepository,
)
from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.claim_repository import CandidateClaim, SqliteClaimRepository
from agentic_trading.financials import (
    extract_available_annual_financial_snapshot,
    infer_annual_period_start,
)
from agentic_trading.migrations import upgrade_database
from agentic_trading.openai_adapter import OpenAIFinancialAnalysisAdapter
from agentic_trading.repository import ResearchRun, SqliteRunRepository
from agentic_trading.sec import CompanyIdentity, FilingMetadata, SecClient
from agentic_trading.source_repository import SourceDocument, SqliteSourceRepository
from agentic_trading.workflow import WorkflowState


@dataclass(frozen=True, slots=True)
class ResearchResult:
    company: CompanyIdentity
    filing: FilingMetadata
    run: ResearchRun
    source: SourceDocument
    claims: tuple[CandidateClaim, ...]
    analysis: AnalysisArtifact


class CompanyResearchService:
    """Run the bounded version-one company research workflow."""

    def __init__(
        self,
        *,
        database_path: Path,
        artifact_root: Path,
        sec_client: SecClient,
        analysis_adapter: OpenAIFinancialAnalysisAdapter,
    ) -> None:
        self._database_path = database_path
        self._artifact_store = LocalArtifactStore(artifact_root)
        self._sec = sec_client
        self._analysis_adapter = analysis_adapter

    def research(self, *, ticker: str, question: str) -> ResearchResult:
        """Research the latest annual filing for *ticker* and persist the run."""
        upgrade_database(self._database_path)
        company = self._sec.resolve_ticker(ticker)
        submissions = self._sec.get_submissions(company.cik)
        filings = self._sec.list_recent_filings(submissions, form="10-K")
        if not filings:
            raise ValueError(f"No 10-K filing found for {company.ticker}")
        filing = filings[0]

        runs = SqliteRunRepository(self._database_path)
        run = runs.create_run(
            memo_id=_memo_id(company, filing),
            as_of=f"{filing.filing_date}T23:59:59Z",
        )
        state = WorkflowState.DRAFT
        try:
            run = runs.transition(
                run.run_id,
                expected_state=state,
                target_state=WorkflowState.COLLECTING_EVIDENCE,
                reason="annual_research_started",
            )
            state = run.state

            source = self._capture_source(company, filing, run.run_id)
            run = runs.transition(
                run.run_id,
                expected_state=state,
                target_state=WorkflowState.EVIDENCE_READY,
                reason="annual_filing_captured",
            )
            state = run.state

            claims, evidence_gaps = self._extract_claims(
                company, filing, run.run_id, source.source_id
            )
            run = runs.transition(
                run.run_id,
                expected_state=state,
                target_state=WorkflowState.ANALYZING,
                reason="financial_claims_extracted",
            )
            state = run.state

            generated = self._analysis_adapter.analyze(
                question=question,
                claims=claims,
                evidence_gaps=evidence_gaps,
            )
            analysis = SqliteAnalysisRepository(
                self._database_path
            ).save_openai_financial_analysis(run_id=run.run_id, generated=generated)
            run = runs.transition(
                run.run_id,
                expected_state=state,
                target_state=WorkflowState.CHALLENGING,
                reason="financial_analysis_completed",
            )
            return ResearchResult(
                company=company,
                filing=filing,
                run=run,
                source=source,
                claims=tuple(claims),
                analysis=analysis,
            )
        except Exception:
            if state not in {WorkflowState.COMPLETE, WorkflowState.FAILED}:
                runs.transition(
                    run.run_id,
                    expected_state=state,
                    target_state=WorkflowState.FAILED,
                    reason="research_failed",
                )
            raise

    def _capture_source(
        self, company: CompanyIdentity, filing: FilingMetadata, run_id: str
    ) -> SourceDocument:
        content = self._sec.get_filing_document(company.cik, filing)
        artifact = self._artifact_store.put(content)
        return SqliteSourceRepository(self._database_path).register(
            run_id=run_id,
            source_type="regulatory_filing",
            title=f"{company.name} {filing.form}",
            publisher="U.S. Securities and Exchange Commission",
            canonical_url=self._sec.filing_url(company.cik, filing),
            source_identifier=f"SEC accession {filing.accession_number}",
            published_at=f"{filing.filing_date}T00:00:00Z",
            retrieved_at=datetime.now(UTC).isoformat(),
            content_sha256=artifact.sha256,
            size_bytes=artifact.size_bytes,
            storage_path=str(artifact.path),
        )

    def _extract_claims(
        self,
        company: CompanyIdentity,
        filing: FilingMetadata,
        run_id: str,
        source_id: str,
    ) -> tuple[list[CandidateClaim], tuple[str, ...]]:
        company_facts = self._sec.get_company_facts(company.cik)
        period_start = infer_annual_period_start(
            company_facts,
            accession_number=filing.accession_number,
            period_end=filing.report_date,
        )
        snapshot, evidence_gaps = extract_available_annual_financial_snapshot(
            company_facts,
            accession_number=filing.accession_number,
            period_start=period_start,
            period_end=filing.report_date,
        )
        repository = SqliteClaimRepository(self._database_path)
        claims = [
            repository.register_xbrl_fact(
                run_id=run_id,
                source_id=source_id,
                fact=fact,
            )
            for fact in snapshot.values()
        ]
        if not claims:
            raise ValueError("No supported annual financial facts were available")
        return claims, evidence_gaps


def _memo_id(company: CompanyIdentity, filing: FilingMetadata) -> str:
    suffix = uuid4().hex[:8]
    return f"memo-{company.ticker.lower()}-{filing.report_date}-{suffix}"
