"""Deterministic extraction of a minimum annual financial snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from agentic_trading.xbrl import (
    FilingFact,
    XbrlFactError,
    list_filing_facts,
    select_filing_fact,
)


@dataclass(frozen=True, slots=True)
class FinancialMetricSpec:
    name: str
    concept: str
    duration: bool
    required: bool = True
    unit: str = "USD"
    taxonomy: str = "us-gaap"
    aliases: tuple[str, ...] = ()


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
        name="business_acquisitions",
        concept="PaymentsToAcquireBusinessesNetOfCashAcquired",
        duration=True,
        required=False,
    ),
    FinancialMetricSpec(
        name="dividends_paid",
        concept="PaymentsOfDividends",
        duration=True,
        required=False,
        aliases=("PaymentsOfDividendsCommonStock",),
    ),
    FinancialMetricSpec(
        name="share_repurchases",
        concept="PaymentsForRepurchaseOfCommonStock",
        duration=True,
        required=False,
    ),
    FinancialMetricSpec(
        name="long_term_debt_issued",
        concept="ProceedsFromIssuanceOfLongTermDebt",
        duration=True,
        required=False,
    ),
    FinancialMetricSpec(
        name="long_term_debt_repaid",
        concept="RepaymentsOfLongTermDebt",
        duration=True,
        required=False,
    ),
    FinancialMetricSpec(
        name="investing_cash_flow",
        concept="NetCashProvidedByUsedInInvestingActivities",
        duration=True,
        required=False,
    ),
    FinancialMetricSpec(
        name="financing_cash_flow",
        concept="NetCashProvidedByUsedInFinancingActivities",
        duration=True,
        required=False,
    ),
    FinancialMetricSpec(
        name="net_change_in_cash",
        concept=(
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
            "PeriodIncreaseDecreaseIncludingExchangeRateEffect"
        ),
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
        fact = _select_metric_fact(
            company_facts,
            metric=metric,
            accession_number=accession_number,
            period_start=period_start,
            period_end=period_end,
        )
        if fact is None:
            gaps.append(f"Missing {metric.name} ({metric.taxonomy}:{metric.concept})")
        else:
            snapshot[metric.name] = fact
    return snapshot, tuple(gaps)


def extract_annual_financial_history(
    company_facts: dict[str, Any],
    *,
    accession_number: str,
    through_period_end: str,
    limit: int = 3,
) -> dict[str, tuple[FilingFact, ...]]:
    """Extract comparable annual periods presented in one exact filing."""
    history: dict[str, tuple[FilingFact, ...]] = {}
    for metric in ANNUAL_FINANCIAL_METRICS:
        facts = _list_metric_facts(
            company_facts,
            metric=metric,
            accession_number=accession_number,
        )
        if facts is None:
            continue
        annual = tuple(
            fact
            for fact in facts
            if fact.period_end <= through_period_end
            and _matches_annual_shape(fact, duration=metric.duration)
        )
        if annual:
            history[metric.name] = annual[-limit:]
    return history


def _select_metric_fact(
    company_facts: dict[str, Any],
    *,
    metric: FinancialMetricSpec,
    accession_number: str,
    period_start: str,
    period_end: str,
) -> FilingFact | None:
    for concept in (metric.concept, *metric.aliases):
        try:
            return select_filing_fact(
                company_facts,
                taxonomy=metric.taxonomy,
                concept=concept,
                unit=metric.unit,
                accession_number=accession_number,
                period_start=period_start if metric.duration else None,
                period_end=period_end,
            )
        except XbrlFactError:
            continue
    return None


def _list_metric_facts(
    company_facts: dict[str, Any],
    *,
    metric: FinancialMetricSpec,
    accession_number: str,
) -> tuple[FilingFact, ...] | None:
    for concept in (metric.concept, *metric.aliases):
        try:
            return list_filing_facts(
                company_facts,
                taxonomy=metric.taxonomy,
                concept=concept,
                unit=metric.unit,
                accession_number=accession_number,
            )
        except XbrlFactError:
            continue
    return None


def _matches_annual_shape(fact: FilingFact, *, duration: bool) -> bool:
    if not duration:
        return fact.period_start is None
    if fact.period_start is None:
        return False
    days = (
        date.fromisoformat(fact.period_end) - date.fromisoformat(fact.period_start)
    ).days
    return 300 <= days <= 380
