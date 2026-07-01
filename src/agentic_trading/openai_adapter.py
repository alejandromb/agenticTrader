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
FINANCIAL_PROMPT_VERSION = "1.1.0"

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


class AnalysisGenerationError(RuntimeError):
    """Raised when provider output is missing or violates domain lineage."""


@dataclass(frozen=True, slots=True)
class GeneratedFinancialAnalysis:
    analysis: FinancialAnalysis
    model: str
    provider_response_id: str
    prompt_version: str
    input_claim_ids: tuple[str, ...]


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
        return GeneratedFinancialAnalysis(
            analysis=analysis,
            model=self.model,
            provider_response_id=response.id,
            prompt_version=FINANCIAL_PROMPT_VERSION,
            input_claim_ids=tuple(sorted(known_claim_ids)),
        )


def _claim_payload(claim: CandidateClaim) -> dict[str, str | None]:
    return {
        "claim_id": claim.claim_id,
        "statement": claim.statement,
        "taxonomy": claim.taxonomy,
        "concept": claim.concept,
        "unit": claim.unit,
        "numeric_value": str(claim.numeric_value),
        "period_start": claim.period_start,
        "period_end": claim.period_end,
        "accession_number": claim.accession_number,
    }
