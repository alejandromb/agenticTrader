from __future__ import annotations

import json
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest
from openai import OpenAIError

from agentic_trading.analysis import AnalysisPoint, FinancialAnalysis
from agentic_trading.claim_repository import CandidateClaim
from agentic_trading.openai_adapter import (
    AnalysisGenerationError,
    OpenAIFinancialAnalysisAdapter,
)


def claim() -> CandidateClaim:
    return CandidateClaim(
        claim_id="claim-001",
        run_id="run-001",
        source_id="source-001",
        claim_type="fact",
        statement="Revenue was 416161000000 USD.",
        taxonomy="us-gaap",
        concept="RevenueFromContractWithCustomerExcludingAssessedTax",
        label="Revenue",
        unit="USD",
        numeric_value=Decimal("416161000000"),
        period_start="2024-09-29",
        period_end="2025-09-27",
        accession_number="0000320193-25-000079",
        extraction_method="sec_companyfacts_v1",
        extracted_at="2026-06-30T16:00:00Z",
    )


class FakeResponses:
    def __init__(self, analysis: FinancialAnalysis | None) -> None:
        self.analysis = analysis
        self.arguments: dict[str, Any] = {}

    def parse(self, **arguments: Any) -> SimpleNamespace:
        self.arguments = arguments
        return SimpleNamespace(id="response-001", output_parsed=self.analysis)


class FailingResponses:
    def parse(self, **_: Any) -> None:
        raise OpenAIError("provider failed")


def test_adapter_uses_structured_responses_and_validates_claims() -> None:
    analysis = FinancialAnalysis(
        assessment="positive",
        summary="Revenue scale is a financial strength.",
        strengths=[AnalysisPoint(text="Large revenue base.", claim_ids=["claim-001"])],
        concerns=[],
        uncertainties=[],
    )
    responses = FakeResponses(analysis)
    client = SimpleNamespace(responses=responses)
    adapter = OpenAIFinancialAnalysisAdapter(client=client, model="test-model")

    result = adapter.analyze(question="Assess financial condition", claims=[claim()])

    assert result.analysis == analysis
    assert result.provider_response_id == "response-001"
    assert result.prompt_version == "1.5.0"
    assert result.input_claim_ids == ("claim-001",)
    assert result.evidence_gaps == ()
    assert responses.arguments["model"] == "test-model"
    assert responses.arguments["text_format"] is FinancialAnalysis
    assert "Use cash_allocation" in responses.arguments["instructions"]
    assert "Use trends" in responses.arguments["instructions"]
    assert "Use known_limitations" in responses.arguments["instructions"]
    payload = json.loads(responses.arguments["input"])
    assert payload["candidate_claims"][0]["claim_id"] == "claim-001"


def test_adapter_cannot_omit_known_evidence_gaps() -> None:
    analysis = FinancialAnalysis(
        assessment="insufficient",
        summary="Evidence is incomplete.",
        strengths=[],
        concerns=[],
        uncertainties=[
            AnalysisPoint(text="Debt evidence is missing.", claim_ids=["claim-001"])
        ],
        known_limitations=[
            "Management guidance was not verified.",
            "Missing total liabilities.",
        ],
    )
    adapter = OpenAIFinancialAnalysisAdapter(
        client=SimpleNamespace(responses=FakeResponses(analysis)), model="test-model"
    )

    result = adapter.analyze(
        question="Assess financial condition",
        claims=[claim()],
        evidence_gaps=["Missing total liabilities"],
    )

    assert result.analysis.known_limitations == [
        "Management guidance was not verified.",
        "Missing total liabilities.",
    ]


def test_unknown_claim_reference_is_rejected() -> None:
    analysis = FinancialAnalysis(
        assessment="insufficient",
        summary="More evidence is required.",
        strengths=[],
        concerns=[],
        uncertainties=[
            AnalysisPoint(text="Missing evidence.", claim_ids=["unknown-claim"])
        ],
    )
    adapter = OpenAIFinancialAnalysisAdapter(
        client=SimpleNamespace(responses=FakeResponses(analysis))
    )

    with pytest.raises(AnalysisGenerationError, match="unknown-claim"):
        adapter.analyze(question="Assess financial condition", claims=[claim()])


def test_empty_claim_input_is_rejected() -> None:
    adapter = OpenAIFinancialAnalysisAdapter(
        client=SimpleNamespace(responses=FakeResponses(None))
    )

    with pytest.raises(ValueError, match="At least one"):
        adapter.analyze(question="Assess financial condition", claims=[])


def test_provider_errors_are_redacted() -> None:
    adapter = OpenAIFinancialAnalysisAdapter(
        client=SimpleNamespace(responses=FailingResponses())
    )

    with pytest.raises(
        AnalysisGenerationError, match="OpenAI request failed: OpenAIError"
    ):
        adapter.analyze(question="Assess financial condition", claims=[claim()])
