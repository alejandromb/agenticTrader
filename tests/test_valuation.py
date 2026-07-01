from decimal import Decimal

from agentic_trading.valuation import calculate_dcf_scenarios


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
