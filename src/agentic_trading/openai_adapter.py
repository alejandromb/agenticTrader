"""Bounded OpenAI adapter for structured financial analysis."""

from __future__ import annotations

import json
import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from openai import OpenAI, OpenAIError

from agentic_trading.analysis import FinancialAnalysis
from agentic_trading.claim_repository import CandidateClaim

DEFAULT_OPENAI_MODEL = "gpt-5.4-2026-03-05"
FINANCIAL_PROMPT_VERSION = "1.5.0"

INSTRUCTIONS = """You are the financial-analysis stage of an investment research system.
Use only the candidate claims provided in the input. Distinguish strengths,
concerns, and uncertainties. Every analytical point must cite one or more input
claim IDs. Do not invent evidence, issue trade instructions, allocate capital,
or claim that returns are guaranteed. Return only the requested structured
analysis."""

INSTRUCTIONS += """
Preserve the exact accounting meaning of each supplied label; do not add
qualifiers such as attribution to parent unless the claim states them. Do not
equate total liabilities with debt or financial leverage. Label any derived
comparison as analysis rather than a reported fact."""

INSTRUCTIONS += """
Respect accounting containment: do not present a component such as cash as an
additional pool separate from a total such as current assets. Do not infer
solvency or conclude that debt is immaterial from debt-to-assets alone; discuss
that comparison only as one limited observation."""

INSTRUCTIONS += """
Use cash_allocation to explain how operating cash was deployed. When operating
cash flow and capital expenditure are available, calculate their difference as
an explicitly derived free-cash-flow approximation and cite both claims. Keep
capital expenditure, acquisitions, dividends, share repurchases, debt issuance,
and debt repayment distinct. A negative investing or financing cash-flow value
means net cash used in that category; it does not by itself mean cash was
destroyed. Do not speculate about the purpose of spending when the supplied
claims do not establish it; identify that missing context as an uncertainty."""

INSTRUCTIONS += """
Use trends only for comparisons supported by claims with distinct periods.
Compare values within the same filing accession by default and state the periods
being compared. Calculate absolute or percentage changes only from cited input
claims. Do not describe a one-period value as a trend, infer a missing period,
or mix filing accessions without explicitly identifying a cross-filing
revision."""

INSTRUCTIONS += """
Use known_limitations to state what could not be verified from the supplied
evidence. Include every known evidence gap without weakening or silently
resolving it. Limitations are not negative conclusions; they define the boundary
of what this analysis can support."""


class AnalysisGenerationError(RuntimeError):
    """Raised when provider output is missing or violates domain lineage."""


@dataclass(frozen=True, slots=True)
class GeneratedFinancialAnalysis:
    analysis: FinancialAnalysis
    model: str
    provider_response_id: str
    prompt_version: str
    input_claim_ids: tuple[str, ...]
    evidence_gaps: tuple[str, ...]


class OpenAIFinancialAnalysisAdapter:
    """Generate validated analysis using the OpenAI Responses API."""

    def __init__(self, client: Any | None = None, model: str | None = None) -> None:
        self._client = client or OpenAI()
        self.model = model or os.environ.get("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    def analyze(
        self,
        *,
        question: str,
        claims: Sequence[CandidateClaim],
        evidence_gaps: Sequence[str] = (),
    ) -> GeneratedFinancialAnalysis:
        """Analyze validated claims and reject unknown output references."""
        if not claims:
            raise ValueError("At least one candidate claim is required")
        known_claim_ids = {claim.claim_id for claim in claims}
        try:
            response = self._client.responses.parse(
                model=self.model,
                instructions=INSTRUCTIONS,
                input=json.dumps(
                    {
                        "investment_question": question,
                        "candidate_claims": [_claim_payload(claim) for claim in claims],
                        "known_evidence_gaps": list(evidence_gaps),
                    },
                    sort_keys=True,
                ),
                text_format=FinancialAnalysis,
            )
        except OpenAIError as error:
            raise AnalysisGenerationError(
                f"OpenAI request failed: {type(error).__name__}"
            ) from error
        analysis = response.output_parsed
        if analysis is None:
            raise AnalysisGenerationError(
                "OpenAI response did not contain parsed output"
            )
        unknown = analysis.referenced_claim_ids() - known_claim_ids
        if unknown:
            references = ", ".join(sorted(unknown))
            raise AnalysisGenerationError(
                f"Analysis referenced unknown claims: {references}"
            )
        limitations = tuple(
            dict.fromkeys(
                [
                    *(item.strip() for item in analysis.known_limitations),
                    *(item.strip() for item in evidence_gaps),
                ]
            )
        )
        analysis = analysis.model_copy(update={"known_limitations": list(limitations)})
        return GeneratedFinancialAnalysis(
            analysis=analysis,
            model=self.model,
            provider_response_id=response.id,
            prompt_version=FINANCIAL_PROMPT_VERSION,
            input_claim_ids=tuple(sorted(known_claim_ids)),
            evidence_gaps=tuple(evidence_gaps),
        )


def _claim_payload(claim: CandidateClaim) -> dict[str, str | None]:
    return {
        "claim_id": claim.claim_id,
        "statement": claim.statement,
        "taxonomy": claim.taxonomy,
        "concept": claim.concept,
        "unit": claim.unit,
        "numeric_value": (
            str(claim.numeric_value) if claim.numeric_value is not None else None
        ),
        "period_start": claim.period_start,
        "period_end": claim.period_end,
        "accession_number": claim.accession_number,
    }
