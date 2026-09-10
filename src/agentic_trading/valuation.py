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


def trailing_value(
    annual: Decimal, prior_ytd: Decimal, current_ytd: Decimal
) -> Decimal:
    """Caller must verify identical metric, currency and comparable periods."""
    if not all(x.is_finite() for x in (annual, prior_ytd, current_ytd)):
        raise ValueError("Finite inputs required")
    return annual - prior_ytd + current_ytd


def cash_flow_sensitivity(
    base: Decimal,
    growth: Decimal,
    discount: Decimal,
    terminal: Decimal,
    years: int = 10,
) -> Decimal:
    """Year-end cash flows plus Gordon terminal value; no net-cash adjustment."""
    if not all(x.is_finite() for x in (base, growth, discount, terminal)):
        raise ValueError("Finite inputs required")
    if base <= 0 or growth <= -1 or terminal <= -1 or discount <= 0:
        raise ValueError("Invalid cash flow or rates")
    if discount <= terminal or type(years) is not int or not 1 <= years <= 100:
        raise ValueError("Require discount > terminal growth and valid horizon")
    cash, value = base, Decimal(0)
    for year in range(1, years + 1):
        cash *= 1 + growth
        value += cash / (1 + discount) ** year
    value += cash * (1 + terminal) / (discount - terminal) / (1 + discount) ** years
    return value


def implied_growth(
    base: Decimal,
    target: Decimal,
    discount: Decimal,
    terminal: Decimal,
    years: int = 10,
) -> Decimal:
    """Bisection within -50% to +100%; conditional implied rate, not forecast."""
    if not target.is_finite() or target <= 0:
        raise ValueError("Positive finite target required")
    low, high = Decimal("-0.5"), Decimal(1)
    if (
        not cash_flow_sensitivity(base, low, discount, terminal, years)
        <= target
        <= cash_flow_sensitivity(base, high, discount, terminal, years)
    ):
        raise ValueError("Target outside search bracket")
    for _ in range(100):
        mid = (low + high) / 2
        if cash_flow_sensitivity(base, mid, discount, terminal, years) < target:
            low = mid
        else:
            high = mid
    return (low + high) / 2
