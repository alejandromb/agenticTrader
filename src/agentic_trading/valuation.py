"""Deterministic valuation scenarios with explicit assumptions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ValuationScenario:
    name: str
    base_cash_flow: Decimal
    annual_growth_rate: Decimal
    discount_rate: Decimal
    terminal_growth_rate: Decimal
    forecast_years: int
    present_value: Decimal
    formula: str


DEFAULT_DCF_ASSUMPTIONS = (
    ("bear", Decimal("0.00"), Decimal("0.12"), Decimal("0.02")),
    ("base", Decimal("0.04"), Decimal("0.10"), Decimal("0.025")),
    ("bull", Decimal("0.07"), Decimal("0.08"), Decimal("0.03")),
)


def calculate_dcf_scenarios(
    base_cash_flow: Decimal, *, forecast_years: int = 5
) -> tuple[ValuationScenario, ...]:
    """Calculate bounded cash-flow present-value scenarios, not equity targets."""
    if base_cash_flow <= 0:
        return ()
    return tuple(
        _calculate_scenario(
            name=name,
            base_cash_flow=base_cash_flow,
            annual_growth_rate=growth,
            discount_rate=discount,
            terminal_growth_rate=terminal_growth,
            forecast_years=forecast_years,
        )
        for name, growth, discount, terminal_growth in DEFAULT_DCF_ASSUMPTIONS
    )


def _calculate_scenario(
    *,
    name: str,
    base_cash_flow: Decimal,
    annual_growth_rate: Decimal,
    discount_rate: Decimal,
    terminal_growth_rate: Decimal,
    forecast_years: int,
) -> ValuationScenario:
    if discount_rate <= terminal_growth_rate:
        raise ValueError("Discount rate must exceed terminal growth rate")
    present_value = Decimal(0)
    projected = base_cash_flow
    for year in range(1, forecast_years + 1):
        projected *= Decimal(1) + annual_growth_rate
        present_value += projected / ((Decimal(1) + discount_rate) ** year)
    terminal_value = (
        projected
        * (Decimal(1) + terminal_growth_rate)
        / (discount_rate - terminal_growth_rate)
    )
    present_value += terminal_value / ((Decimal(1) + discount_rate) ** forecast_years)
    return ValuationScenario(
        name=name,
        base_cash_flow=base_cash_flow,
        annual_growth_rate=annual_growth_rate,
        discount_rate=discount_rate,
        terminal_growth_rate=terminal_growth_rate,
        forecast_years=forecast_years,
        present_value=present_value.quantize(Decimal("1")),
        formula=(
            "sum(base_cash_flow * (1 + annual_growth_rate)^year / "
            "(1 + discount_rate)^year) + terminal_value / "
            "(1 + discount_rate)^forecast_years"
        ),
    )
