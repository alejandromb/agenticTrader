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
from agentic_trading.calculations import calculate_financial_history
from agentic_trading.claim_repository import CandidateClaim, SqliteClaimRepository
from agentic_trading.filing_narrative import (
    extract_capital_allocation_statements,
    extract_capital_allocation_table_details,
)
from agentic_trading.filing_sections import extract_business_and_risk_evidence
from agentic_trading.financials import (
    extract_annual_financial_history,
    extract_available_annual_financial_snapshot,
    extract_available_quarterly_financial_snapshot,
    extract_quarterly_financial_history,
    infer_annual_period_start,
    require_filing_fact_coverage,
)
from agentic_trading.memo_repository import (
    InvestmentMemoArtifact,
    SqliteInvestmentMemoRepository,
)
from agentic_trading.migrations import upgrade_database
from agentic_trading.openai_adapter import OpenAIFinancialAnalysisAdapter
from agentic_trading.repository import ResearchRun, SqliteRunRepository
from agentic_trading.revision_repository import (
    RevisionAudit,
    SqliteRevisionAuditRepository,
)
from agentic_trading.sec import CompanyIdentity, FilingMetadata, SecClient
from agentic_trading.source_repository import SourceDocument, SqliteSourceRepository
from agentic_trading.valuation import calculate_dcf_scenarios
from agentic_trading.workflow import WorkflowState
from agentic_trading.xbrl import (
    FilingFact,
    compare_filing_facts,
    find_original_filing_fact,
)


@dataclass(frozen=True, slots=True)
class ResearchResult:
    company: CompanyIdentity
    filing: FilingMetadata
    run: ResearchRun
    source: SourceDocument
    claims: tuple[CandidateClaim, ...]
    revision_audits: tuple[RevisionAudit, ...]
    analysis: AnalysisArtifact
    memo: InvestmentMemoArtifact


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

    def research(
        self, *, ticker: str, question: str, form: str = "10-K"
    ) -> ResearchResult:
        """Research the latest explicitly selected filing for *ticker*."""
        if form not in {"10-K", "10-Q"}:
            raise ValueError("Research form must be 10-K or 10-Q")
        upgrade_database(self._database_path)
        company = self._sec.resolve_ticker(ticker)
        submissions = self._sec.get_submissions(company.cik)
        filings = self._sec.list_recent_filings(submissions, form=form)
        if not filings:
            raise ValueError(f"No {form} filing found for {company.ticker}")
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
                reason=f"{form.lower().replace('-', '')}_research_started",
            )
            state = run.state

            source = self._capture_source(company, filing, run.run_id)
            run = runs.transition(
                run.run_id,
                expected_state=state,
                target_state=WorkflowState.EVIDENCE_READY,
                reason=f"{form.lower().replace('-', '')}_filing_captured",
            )
            state = run.state

            claims, evidence_gaps, revision_audits = self._extract_claims(
                company, filing, run.run_id, source
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
                revision_audits=revision_audits,
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
            state = run.state
            run = runs.transition(
                run.run_id,
                expected_state=state,
                target_state=WorkflowState.SYNTHESIZING,
                reason="company_analysis_challenged",
            )
            state = run.state
            memo = SqliteInvestmentMemoRepository(
                self._database_path
            ).synthesize_and_save(
                run=run,
                company=company,
                question=question,
                source=source,
                claims=claims,
                analysis=analysis,
            )
            run = runs.transition(
                run.run_id,
                expected_state=state,
                target_state=WorkflowState.VALIDATING,
                reason="investment_memo_synthesized",
            )
            state = run.state
            run = runs.transition(
                run.run_id,
                expected_state=state,
                target_state=WorkflowState.AWAITING_HUMAN_DISPOSITION,
                reason="investment_memo_validated",
            )
            return ResearchResult(
                company=company,
                filing=filing,
                run=run,
                source=source,
                claims=tuple(claims),
                revision_audits=tuple(revision_audits),
                analysis=analysis,
                memo=memo,
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
        source: SourceDocument,
    ) -> tuple[list[CandidateClaim], tuple[str, ...], list[RevisionAudit]]:
        if filing.form == "10-Q":
            return self._extract_quarterly_claims(company, filing, run_id, source)
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
        claims: list[CandidateClaim] = []
        fact_claim_ids: dict[tuple[str, str | None, str, str], str] = {}
        for fact in snapshot.values():
            claim = repository.register_xbrl_fact(
                run_id=run_id, source_id=source.source_id, fact=fact
            )
            claims.append(claim)
            fact_claim_ids[_fact_key(fact)] = claim.claim_id
        history = extract_annual_financial_history(
            company_facts,
            accession_number=filing.accession_number,
            through_period_end=filing.report_date,
        )
        audit_repository = SqliteRevisionAuditRepository(self._database_path)
        revision_audits: list[RevisionAudit] = []
        for facts in history.values():
            for later in facts:
                original = find_original_filing_fact(company_facts, later=later)
                if original is None:
                    continue
                revision = compare_filing_facts(original, later)
                if revision is not None:
                    revision_audits.append(audit_repository.register(run_id, revision))
        current_fact_keys = {
            (fact.concept, fact.period_start, fact.period_end)
            for fact in snapshot.values()
        }
        for facts in history.values():
            for fact in facts:
                if (
                    fact.concept,
                    fact.period_start,
                    fact.period_end,
                ) in current_fact_keys:
                    continue
                claim = repository.register_xbrl_fact(
                    run_id=run_id, source_id=source.source_id, fact=fact
                )
                claims.append(claim)
                fact_claim_ids[_fact_key(fact)] = claim.claim_id
        free_cash_flow_claims: list[CandidateClaim] = []
        for calculation in calculate_financial_history(history):
            input_claim_ids = tuple(
                fact_claim_ids[_fact_key(fact)] for fact in calculation.input_facts
            )
            claim = repository.register_calculation(
                run_id=run_id,
                source_id=source.source_id,
                calculation=calculation,
                input_claim_ids=input_claim_ids,
            )
            claims.append(claim)
            if calculation.concept == "free_cash_flow_approximation":
                free_cash_flow_claims.append(claim)
        if free_cash_flow_claims:
            base_claim = max(free_cash_flow_claims, key=lambda item: item.period_end)
            if base_claim.numeric_value is not None:
                claims.extend(
                    repository.register_valuation_scenario(
                        run_id=run_id,
                        source_id=source.source_id,
                        scenario=scenario,
                        input_claim_id=base_claim.claim_id,
                        period_end=base_claim.period_end,
                        accession_number=base_claim.accession_number,
                    )
                    for scenario in calculate_dcf_scenarios(base_claim.numeric_value)
                )
        filing_content = Path(source.storage_path).read_bytes()
        statements = extract_capital_allocation_statements(filing_content)
        claims.extend(
            repository.register_filing_statement(
                run_id=run_id,
                source_id=source.source_id,
                statement=statement,
                topic="capital_allocation_purpose",
                period_end=filing.report_date,
                accession_number=filing.accession_number,
                sequence=sequence,
            )
            for sequence, statement in enumerate(statements, start=1)
        )
        details = extract_capital_allocation_table_details(filing_content)
        claims.extend(
            repository.register_filing_statement(
                run_id=run_id,
                source_id=source.source_id,
                statement=detail,
                topic="capital_allocation_detail",
                period_end=filing.report_date,
                accession_number=filing.accession_number,
                sequence=sequence,
            )
            for sequence, detail in enumerate(details, start=1)
        )
        section_evidence = extract_business_and_risk_evidence(filing_content)
        for topic, statements in (
            ("business_evidence", section_evidence.business),
            ("risk_evidence", section_evidence.risks),
        ):
            claims.extend(
                repository.register_filing_statement(
                    run_id=run_id,
                    source_id=source.source_id,
                    statement=statement,
                    topic=topic,
                    period_end=filing.report_date,
                    accession_number=filing.accession_number,
                    sequence=sequence,
                )
                for sequence, statement in enumerate(statements, start=1)
            )
        if not section_evidence.business:
            evidence_gaps += ("Item 1 business evidence was not extracted",)
        if not section_evidence.risks:
            evidence_gaps += ("Item 1A risk evidence was not extracted",)
        if "capital_expenditure" in snapshot and not statements:
            evidence_gaps += (
                "Capital expenditure purpose was not found in deterministic "
                "filing extraction",
            )
        if not claims:
            raise ValueError("No supported annual financial facts were available")
        return claims, evidence_gaps, revision_audits

    def _extract_quarterly_claims(
        self,
        company: CompanyIdentity,
        filing: FilingMetadata,
        run_id: str,
        source: SourceDocument,
    ) -> tuple[list[CandidateClaim], tuple[str, ...], list[RevisionAudit]]:
        """Persist a 10-Q update without annualizing or creating a DCF."""
        company_facts = self._sec.get_company_facts(company.cik)
        require_filing_fact_coverage(
            company_facts, accession_number=filing.accession_number
        )
        snapshot, evidence_gaps = extract_available_quarterly_financial_snapshot(
            company_facts,
            accession_number=filing.accession_number,
            period_end=filing.report_date,
        )
        history = extract_quarterly_financial_history(
            company_facts,
            accession_number=filing.accession_number,
            through_period_end=filing.report_date,
        )
        repository = SqliteClaimRepository(self._database_path)
        claims: list[CandidateClaim] = []
        fact_claim_ids: dict[tuple[str, str | None, str, str], str] = {}
        current_keys = {
            (fact.concept, fact.period_start, fact.period_end)
            for fact in snapshot.values()
        }
        for metric_name, fact in snapshot.items():
            claim = repository.register_xbrl_fact(
                run_id=run_id,
                source_id=source.source_id,
                fact=fact,
                statement=_quarterly_fact_statement(metric_name, fact),
            )
            claims.append(claim)
            fact_claim_ids[_fact_key(fact)] = claim.claim_id
        for metric_name, facts in history.items():
            for fact in facts:
                if (fact.concept, fact.period_start, fact.period_end) in current_keys:
                    continue
                claim = repository.register_xbrl_fact(
                    run_id=run_id,
                    source_id=source.source_id,
                    fact=fact,
                    statement=_quarterly_fact_statement(metric_name, fact),
                )
                claims.append(claim)
                fact_claim_ids[_fact_key(fact)] = claim.claim_id

        audit_repository = SqliteRevisionAuditRepository(self._database_path)
        revision_audits: list[RevisionAudit] = []
        for facts in history.values():
            for later in facts:
                original = find_original_filing_fact(company_facts, later=later)
                if original is None:
                    continue
                revision = compare_filing_facts(original, later)
                if revision is not None:
                    revision_audits.append(audit_repository.register(run_id, revision))

        for calculation in calculate_financial_history(history):
            input_claim_ids = tuple(
                fact_claim_ids[_fact_key(fact)] for fact in calculation.input_facts
            )
            claims.append(
                repository.register_calculation(
                    run_id=run_id,
                    source_id=source.source_id,
                    calculation=calculation,
                    input_claim_ids=input_claim_ids,
                )
            )
        evidence_gaps += (
            "Quarterly update does not include a complete annual business-model "
            "evidence refresh",
            "Quarterly update does not include a complete annual risk-factor "
            "evidence refresh",
            "Capital-allocation narrative was not extracted from the quarterly filing",
        )
        if not claims:
            raise ValueError("No supported quarterly financial facts were available")
        return claims, evidence_gaps, revision_audits


def _memo_id(company: CompanyIdentity, filing: FilingMetadata) -> str:
    suffix = uuid4().hex[:8]
    return f"memo-{company.ticker.lower()}-{filing.report_date}-{suffix}"


def _quarterly_fact_statement(metric_name: str, fact: FilingFact) -> str:
    if fact.period_start is None:
        context = "quarter-end instant"
    else:
        from datetime import date

        days = (
            date.fromisoformat(fact.period_end)
            - date.fromisoformat(fact.period_start)
        ).days
        context = "discrete quarter" if days <= 120 else "year-to-date"
    return (
        f"{metric_name.replace('_', ' ').title()} was {fact.value} {fact.unit} "
        f"for the {context} context ending {fact.period_end}."
    )


def _fact_key(fact: FilingFact) -> tuple[str, str | None, str, str]:
    return (
        fact.concept,
        fact.period_start,
        fact.period_end,
        fact.accession_number,
    )
