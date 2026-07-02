"""Deterministic financial calculations with explicit fact inputs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from agentic_trading.xbrl import FilingFact

_SIX_PLACES = Decimal("0.000001")


@dataclass(frozen=True, slots=True)
class DerivedCalculation:
    concept: str
    label: str
    formula: str
    value: Decimal
    unit: str
    period_start: str | None
    period_end: str
    accession_number: str
    input_facts: tuple[FilingFact, ...]


def calculate_financial_history(
    history: dict[str, tuple[FilingFact, ...]],
) -> tuple[DerivedCalculation, ...]:
    """Calculate metrics only from compatible exact-period inputs."""
    calculations: list[DerivedCalculation] = []
    calculations.extend(_growth(history.get("revenue", ())))
    calculations.extend(
        _ratio_by_period(
            history,
            numerator="operating_income",
            denominator="revenue",
            concept="operating_margin",
            label="Operating margin",
        )
    )
    calculations.extend(
        _ratio_by_period(
            history,
            numerator="net_income",
            denominator="revenue",
            concept="net_margin",
            label="Net margin",
        )
    )
    calculations.extend(_free_cash_flow(history))
    calculations.extend(
        _ratio_by_period(
            history,
            numerator="current_assets",
            denominator="current_liabilities",
            concept="current_ratio",
            label="Current ratio",
            percent=False,
        )
    )
    return tuple(calculations)


def _growth(facts: tuple[FilingFact, ...]) -> list[DerivedCalculation]:
    values: list[DerivedCalculation] = []
    for prior, current in zip(facts, facts[1:], strict=False):
        if prior.value == 0 or not _compatible_duration_shape(prior, current):
            continue
        value = ((current.value - prior.value) / abs(prior.value) * 100).quantize(
            _SIX_PLACES
        )
        values.append(
            _calculation(
                concept="revenue_growth",
                label="Revenue growth",
                formula="(current_revenue - prior_revenue) / abs(prior_revenue) * 100",
                value=value,
                unit="percent",
                inputs=(prior, current),
                period_start=current.period_start,
                period_end=current.period_end,
            )
        )
    return values


def _ratio_by_period(
    history: dict[str, tuple[FilingFact, ...]],
    *,
    numerator: str,
    denominator: str,
    concept: str,
    label: str,
    percent: bool = True,
) -> list[DerivedCalculation]:
    denominators = {
        (fact.period_start, fact.period_end): fact
        for fact in history.get(denominator, ())
    }
    values = []
    for numerator_fact in history.get(numerator, ()):
        denominator_fact = denominators.get(
            (numerator_fact.period_start, numerator_fact.period_end)
        )
        if denominator_fact is None or denominator_fact.value == 0:
            continue
        multiplier = Decimal(100) if percent else Decimal(1)
        value = (numerator_fact.value / denominator_fact.value * multiplier).quantize(
            _SIX_PLACES
        )
        values.append(
            _calculation(
                concept=concept,
                label=label,
                formula=f"{numerator} / {denominator}" + (" * 100" if percent else ""),
                value=value,
                unit="percent" if percent else "ratio",
                inputs=(numerator_fact, denominator_fact),
                period_start=numerator_fact.period_start,
                period_end=numerator_fact.period_end,
            )
        )
    return values


def _free_cash_flow(
    history: dict[str, tuple[FilingFact, ...]],
) -> list[DerivedCalculation]:
    capex = {
        (fact.period_start, fact.period_end): fact
        for fact in history.get("capital_expenditure", ())
    }
    values = []
    for cash_flow in history.get("operating_cash_flow", ()):
        capital_expenditure = capex.get(
            (cash_flow.period_start, cash_flow.period_end)
        )
        if capital_expenditure is None:
            continue
        values.append(
            _calculation(
                concept="free_cash_flow_approximation",
                label="Free cash flow approximation",
                formula="operating_cash_flow - capital_expenditure",
                value=cash_flow.value - capital_expenditure.value,
                unit="USD",
                inputs=(cash_flow, capital_expenditure),
                period_start=cash_flow.period_start,
                period_end=cash_flow.period_end,
            )
        )
    return values


def _calculation(
    *,
    concept: str,
    label: str,
    formula: str,
    value: Decimal,
    unit: str,
    inputs: tuple[FilingFact, ...],
    period_start: str | None,
    period_end: str,
) -> DerivedCalculation:
    accessions = {fact.accession_number for fact in inputs}
    if len(accessions) != 1:
        raise ValueError("Calculation inputs must share one filing accession")
    return DerivedCalculation(
        concept=concept,
        label=label,
        formula=formula,
        value=value,
        unit=unit,
        period_start=period_start,
        period_end=period_end,
        accession_number=next(iter(accessions)),
        input_facts=inputs,
    )


def _compatible_duration_shape(left: FilingFact, right: FilingFact) -> bool:
    if (
        left.form == right.form == "10-K"
        and left.fiscal_period == right.fiscal_period == "FY"
    ):
        return True
    if left.period_start is None or right.period_start is None:
        return left.period_start is right.period_start
    left_days = (
        date.fromisoformat(left.period_end) - date.fromisoformat(left.period_start)
    ).days
    right_days = (
        date.fromisoformat(right.period_end) - date.fromisoformat(right.period_start)
    ).days
    return abs(left_days - right_days) <= 7
