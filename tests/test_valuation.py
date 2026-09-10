from decimal import Decimal
from decimal import Decimal as D

import pytest

from agentic_trading.valuation import (
    calculate_dcf_scenarios,
    cash_flow_sensitivity,
    implied_growth,
    trailing_value,
)


def test_dcf_scenarios_are_ordered_and_assumptions_are_explicit() -> None:
    scenarios = calculate_dcf_scenarios(Decimal("100"))

    assert [scenario.name for scenario in scenarios] == ["bear", "base", "bull"]
    assert scenarios[0].present_value < scenarios[1].present_value
    assert scenarios[1].present_value < scenarios[2].present_value
    assert scenarios[1].annual_growth_rate == Decimal("0.04")
    assert scenarios[1].discount_rate == Decimal("0.10")
    assert scenarios[1].terminal_growth_rate == Decimal("0.025")
    assert "terminal_value" in scenarios[1].formula


def test_nonpositive_cash_flow_does_not_create_false_valuation() -> None:
    assert calculate_dcf_scenarios(Decimal("0")) == ()


def test_bridge():
    assert trailing_value(D("3030.5"), D("1297.0"), D("1972.9")) == D("3706.4")
    assert trailing_value(D("539.8"), D("271.9"), D("215.9")) == D("483.8")


def test_flat_perpetuity():
    assert abs(cash_flow_sensitivity(D(10), D(0), D(".1"), D(0)) - D(100)) < D("1e-20")


def test_reverse_round_trip():
    value = cash_flow_sensitivity(D(100), D(".15"), D(".1"), D(".03"))
    assert abs(implied_growth(D(100), value, D(".1"), D(".03")) - D(".15")) < D("1e-20")


@pytest.mark.parametrize("r,g", [(".03", ".03"), ("0", "0"), ("NaN", ".03")])
def test_invalid_discount(r, g):
    with pytest.raises(ValueError):
        cash_flow_sensitivity(D(100), D(".1"), D(r), D(g))
