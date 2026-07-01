"""Deterministic extraction of a minimum annual financial snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from agentic_trading.xbrl import FilingFact, XbrlFactError, select_filing_fact


@dataclass(frozen=True, slots=True)
class FinancialMetricSpec:
    name: str
    concept: str
    duration: bool
    required: bool = True
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
    FinancialMetricSpec(
        name="cash_and_cash_equivalents",
        concept="CashAndCashEquivalentsAtCarryingValue",
        duration=False,
        required=False,
    ),
    FinancialMetricSpec(
        name="current_assets",
        concept="AssetsCurrent",
        duration=False,
        required=False,
    ),
    FinancialMetricSpec(
        name="current_liabilities",
        concept="LiabilitiesCurrent",
        duration=False,
        required=False,
    ),
    FinancialMetricSpec(
        name="operating_income",
        concept="OperatingIncomeLoss",
        duration=True,
        required=False,
    ),
    FinancialMetricSpec(
        name="capital_expenditure",
        concept="PaymentsToAcquirePropertyPlantAndEquipment",
        duration=True,
        required=False,
    ),
    FinancialMetricSpec(
        name="current_long_term_debt",
        concept="LongTermDebtCurrent",
        duration=False,
        required=False,
    ),
    FinancialMetricSpec(
        name="noncurrent_long_term_debt",
        concept="LongTermDebtNoncurrent",
        duration=False,
        required=False,
    ),
)


def infer_annual_period_start(
    company_facts: dict[str, Any], *, accession_number: str, period_end: str
) -> str:
    """Infer the annual duration start from the filing's revenue observation."""
    revenue = select_filing_fact(
        company_facts,
        taxonomy="us-gaap",
        concept="RevenueFromContractWithCustomerExcludingAssessedTax",
        unit="USD",
        accession_number=accession_number,
        period_end=period_end,
    )
    if revenue.period_start is None:
        raise ValueError("Annual revenue observation has no period start")
    return revenue.period_start


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
        if metric.required
    }


def extract_available_annual_financial_snapshot(
    company_facts: dict[str, Any],
    *,
    accession_number: str,
    period_start: str,
    period_end: str,
) -> tuple[dict[str, FilingFact], tuple[str, ...]]:
    """Extract available metrics and report issuer-specific concept gaps."""
    snapshot: dict[str, FilingFact] = {}
    gaps: list[str] = []
    for metric in ANNUAL_FINANCIAL_METRICS:
        try:
            snapshot[metric.name] = select_filing_fact(
                company_facts,
                taxonomy=metric.taxonomy,
                concept=metric.concept,
                unit=metric.unit,
                accession_number=accession_number,
                period_start=period_start if metric.duration else None,
                period_end=period_end,
            )
        except XbrlFactError:
            gaps.append(f"Missing {metric.name} ({metric.taxonomy}:{metric.concept})")
    return snapshot, tuple(gaps)
