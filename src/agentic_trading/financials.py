"""Deterministic extraction of a minimum annual financial snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentic_trading.xbrl import FilingFact, select_filing_fact


@dataclass(frozen=True, slots=True)
class FinancialMetricSpec:
    name: str
    concept: str
    duration: bool
    unit: str = "USD"
    taxonomy: str = "us-gaap"


ANNUAL_FINANCIAL_METRICS = (
    FinancialMetricSpec(
        name="revenue",
        concept="RevenueFromContractWithCustomerExcludingAssessedTax",
        duration=True,
    ),
    FinancialMetricSpec(name="net_income", concept="NetIncomeLoss", duration=True),
    FinancialMetricSpec(name="assets", concept="Assets", duration=False),
    FinancialMetricSpec(name="liabilities", concept="Liabilities", duration=False),
    FinancialMetricSpec(
        name="operating_cash_flow",
        concept="NetCashProvidedByUsedInOperatingActivities",
        duration=True,
    ),
)


def extract_annual_financial_snapshot(
    company_facts: dict[str, Any],
    *,
    accession_number: str,
    period_start: str,
    period_end: str,
) -> dict[str, FilingFact]:
    """Extract the required annual financial metrics for one exact filing."""
    return {
        metric.name: select_filing_fact(
            company_facts,
            taxonomy=metric.taxonomy,
            concept=metric.concept,
            unit=metric.unit,
            accession_number=accession_number,
            period_start=period_start if metric.duration else None,
            period_end=period_end,
        )
        for metric in ANNUAL_FINANCIAL_METRICS
    }
