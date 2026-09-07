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

_DISCRETE_QUARTER_METRICS = {"revenue", "net_income", "operating_income"}


def require_filing_fact_coverage(
    company_facts: dict[str, Any], *, accession_number: str
) -> None:
    """Distinguish absent upstream filing coverage from unsupported concepts."""
    for concepts in company_facts.get("facts", {}).values():
        for item in concepts.values():
            for observations in item.get("units", {}).values():
                if any(row.get("accn") == accession_number for row in observations):
                    return
    raise ValueError(
        f"SEC company-facts response has no observations for filing "
        f"{accession_number}; upstream filing coverage is unavailable. "
        "No older filing was substituted."
    )


def _metric_concepts(
    company_facts: dict[str, Any], metric: FinancialMetricSpec, accession: str
) -> tuple[str, ...]:
    concepts = (metric.concept, *metric.aliases)
    # Reviewed cash-flow statement labels this exact filing's ProductiveAssets
    # as purchases of PP&E. Do not generalize the broader taxonomy concept.
    # https://www.sec.gov/Archives/edgar/data/1035267/
    # 000103526726000058/isrg-20260630.htm
    if (
        str(company_facts.get("cik", "")).lstrip("0") == "1035267"
        and accession == "0001035267-26-000058"
        and metric.name == "capital_expenditure"
    ):
        concepts += ("PaymentsToAcquireProductiveAssets",)
    return concepts


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


def extract_available_quarterly_financial_snapshot(
    company_facts: dict[str, Any],
    *,
    accession_number: str,
    period_end: str,
) -> tuple[dict[str, FilingFact], tuple[str, ...]]:
    """Select discrete, YTD, and instant facts from one exact Form 10-Q."""
    snapshot: dict[str, FilingFact] = {}
    gaps: list[str] = []
    for metric in ANNUAL_FINANCIAL_METRICS:
        fact = _select_quarterly_metric_fact(
            company_facts,
            metric=metric,
            accession_number=accession_number,
            period_end=period_end,
        )
        if fact is None:
            gaps.append(f"Missing {metric.name} ({metric.taxonomy}:{metric.concept})")
        else:
            snapshot[metric.name] = fact
    return snapshot, tuple(gaps)


def extract_quarterly_financial_history(
    company_facts: dict[str, Any],
    *,
    accession_number: str,
    through_period_end: str,
    limit: int = 4,
) -> dict[str, tuple[FilingFact, ...]]:
    """Extract compatible quarterly contexts presented in one Form 10-Q."""
    history: dict[str, tuple[FilingFact, ...]] = {}
    for metric in ANNUAL_FINANCIAL_METRICS:
        facts = _list_metric_facts(
            company_facts,
            metric=metric,
            accession_number=accession_number,
            form="10-Q",
        )
        if facts is None:
            continue
        eligible = [fact for fact in facts if fact.period_end <= through_period_end]
        if metric.duration:
            eligible = [
                fact
                for fact in eligible
                if _matches_quarterly_shape(
                    fact, discrete=metric.name in _DISCRETE_QUARTER_METRICS
                )
            ]
            by_end: dict[str, FilingFact] = {}
            for fact in eligible:
                current = by_end.get(fact.period_end)
                if current is None:
                    by_end[fact.period_end] = fact
                    continue
                if metric.name in _DISCRETE_QUARTER_METRICS:
                    if _duration_days(fact) < _duration_days(current):
                        by_end[fact.period_end] = fact
                elif _duration_days(fact) > _duration_days(current):
                    by_end[fact.period_end] = fact
            eligible = [by_end[key] for key in sorted(by_end)]
        else:
            eligible = [fact for fact in eligible if fact.period_start is None]
        if eligible:
            history[metric.name] = tuple(eligible[-limit:])
    return history


def _select_metric_fact(
    company_facts: dict[str, Any],
    *,
    metric: FinancialMetricSpec,
    accession_number: str,
    period_start: str,
    period_end: str,
) -> FilingFact | None:
    for concept in _metric_concepts(company_facts, metric, accession_number):
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
    form: str = "10-K",
) -> tuple[FilingFact, ...] | None:
    for concept in _metric_concepts(company_facts, metric, accession_number):
        try:
            facts = list_filing_facts(
                company_facts,
                taxonomy=metric.taxonomy,
                concept=concept,
                unit=metric.unit,
                accession_number=accession_number,
                form=form,
            )
            if facts:
                return facts
        except XbrlFactError:
            continue
    return None


def _select_quarterly_metric_fact(
    company_facts: dict[str, Any],
    *,
    metric: FinancialMetricSpec,
    accession_number: str,
    period_end: str,
) -> FilingFact | None:
    facts = _list_metric_facts(
        company_facts,
        metric=metric,
        accession_number=accession_number,
        form="10-Q",
    )
    if facts is None:
        return None
    ending = [fact for fact in facts if fact.period_end == period_end]
    if not metric.duration:
        instant = [fact for fact in ending if fact.period_start is None]
        return instant[0] if len(instant) == 1 else None
    candidates = [
        fact
        for fact in ending
        if _matches_quarterly_shape(
            fact, discrete=metric.name in _DISCRETE_QUARTER_METRICS
        )
    ]
    if not candidates:
        return None
    if metric.name in _DISCRETE_QUARTER_METRICS:
        return min(candidates, key=_duration_days)
    return max(candidates, key=_duration_days)


def _matches_annual_shape(fact: FilingFact, *, duration: bool) -> bool:
    if not duration:
        return fact.period_start is None
    if fact.period_start is None:
        return False
    days = (
        date.fromisoformat(fact.period_end) - date.fromisoformat(fact.period_start)
    ).days
    return 300 <= days <= 380


def _matches_quarterly_shape(fact: FilingFact, *, discrete: bool) -> bool:
    if fact.period_start is None:
        return False
    days = _duration_days(fact)
    return 60 <= days <= (120 if discrete else 300)


def _duration_days(fact: FilingFact) -> int:
    if fact.period_start is None:
        raise ValueError("Duration fact requires a period start")
    return (
        date.fromisoformat(fact.period_end) - date.fromisoformat(fact.period_start)
    ).days
