from __future__ import annotations

from pathlib import Path
from typing import Any

from agentic_trading.analysis import AnalysisPoint, FinancialAnalysis
from agentic_trading.openai_adapter import GeneratedFinancialAnalysis
from agentic_trading.research import CompanyResearchService
from agentic_trading.sec import CompanyIdentity, FilingMetadata
from agentic_trading.workflow import WorkflowState


class FakeSecClient:
    filing = FilingMetadata(
        accession_number="0000320193-25-000079",
        form="10-K",
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl-20250927.htm",
    )

    def resolve_ticker(self, ticker: str) -> CompanyIdentity:
        assert ticker == "AAPL"
        return CompanyIdentity(cik="0000320193", ticker="AAPL", name="Apple Inc.")

    def get_submissions(self, cik: str) -> dict[str, Any]:
        assert cik == "0000320193"
        return {"filings": "fake"}

    def list_recent_filings(
        self, submissions: dict[str, Any], *, form: str | None = None
    ) -> list[FilingMetadata]:
        assert submissions == {"filings": "fake"}
        assert form == "10-K"
        return [self.filing]

    def get_filing_document(self, cik: str, filing: FilingMetadata) -> bytes:
        assert cik == "0000320193"
        assert filing == self.filing
        return b"<html>Apple filing</html>"

    def filing_url(self, cik: str, filing: FilingMetadata) -> str:
        return f"https://www.sec.gov/{cik}/{filing.primary_document}"

    def get_company_facts(self, cik: str) -> dict[str, Any]:
        assert cik == "0000320193"
        concepts = {
            "RevenueFromContractWithCustomerExcludingAssessedTax": 416161000000,
            "NetIncomeLoss": 112010000000,
            "Assets": 359241000000,
            "Liabilities": 285508000000,
            "NetCashProvidedByUsedInOperatingActivities": 111482000000,
        }
        instant = {"Assets", "Liabilities"}
        facts: dict[str, Any] = {"facts": {"us-gaap": {}}}
        for concept, value in concepts.items():
            observation: dict[str, Any] = {
                "end": "2025-09-27",
                "val": value,
                "accn": self.filing.accession_number,
                "fy": 2025,
                "fp": "FY",
                "form": "10-K",
                "filed": "2025-10-31",
            }
            if concept not in instant:
                observation["start"] = "2024-09-29"
            facts["facts"]["us-gaap"][concept] = {
                "label": concept,
                "units": {"USD": [observation]},
            }
        return facts


class FakeAnalysisAdapter:
    def analyze(
        self,
        *,
        question: str,
        claims: list[Any],
        evidence_gaps: tuple[str, ...],
    ) -> GeneratedFinancialAnalysis:
        assert question == "Assess Apple"
        assert evidence_gaps == ()
        claim_ids = tuple(sorted(claim.claim_id for claim in claims))
        return GeneratedFinancialAnalysis(
            analysis=FinancialAnalysis(
                assessment="mixed",
                summary="Strong scale with incomplete evidence.",
                strengths=[
                    AnalysisPoint(text="Large scale.", claim_ids=[claim_ids[0]])
                ],
                concerns=[],
                uncertainties=[
                    AnalysisPoint(text="More history needed.", claim_ids=[claim_ids[1]])
                ],
            ),
            model="test-model",
            provider_response_id="response-001",
            prompt_version="1.1.0",
            input_claim_ids=claim_ids,
            evidence_gaps=evidence_gaps,
        )


def test_research_company_runs_end_to_end(tmp_path: Path) -> None:
    service = CompanyResearchService(
        database_path=tmp_path / "state.db",
        artifact_root=tmp_path / "artifacts",
        sec_client=FakeSecClient(),
        analysis_adapter=FakeAnalysisAdapter(),
    )

    result = service.research(ticker="AAPL", question="Assess Apple")

    assert result.company.ticker == "AAPL"
    assert result.run.state is WorkflowState.CHALLENGING
    assert len(result.claims) == 5
    assert result.analysis.prompt_version == "1.1.0"
    assert Path(result.source.storage_path).exists()
