from decimal import Decimal

from agentic_trading.calculations import calculate_financial_history
from agentic_trading.xbrl import FilingFact


def fact(concept: str, value: str, end: str, start: str | None = "2024-01-01"):
    return FilingFact(
        taxonomy="us-gaap",
        concept=concept,
        label=concept,
        unit="USD",
        value=Decimal(value),
        period_start=start,
        period_end=end,
        filed="2026-01-01",
        form="10-K",
        accession_number="accession",
        fiscal_year=2025,
        fiscal_period="FY",
    )


def test_calculates_growth_margins_cash_flow_and_liquidity() -> None:
    history = {
        "revenue": (
            fact("Revenue", "100", "2024-12-31"),
            fact("Revenue", "110", "2025-12-31"),
        ),
        "operating_income": (fact("OperatingIncome", "22", "2025-12-31"),),
        "net_income": (fact("NetIncome", "11", "2025-12-31"),),
        "operating_cash_flow": (fact("OperatingCashFlow", "20", "2025-12-31"),),
        "capital_expenditure": (fact("CapitalExpenditure", "8", "2025-12-31"),),
        "current_assets": (fact("CurrentAssets", "60", "2025-12-31", None),),
        "current_liabilities": (fact("CurrentLiabilities", "40", "2025-12-31", None),),
    }

    calculations = {item.concept: item for item in calculate_financial_history(history)}

    assert calculations["revenue_growth"].value == Decimal("10.000000")
    assert calculations["operating_margin"].value == Decimal("20.000000")
    assert calculations["net_margin"].value == Decimal("10.000000")
    assert calculations["free_cash_flow_approximation"].value == Decimal("12")
    assert calculations["current_ratio"].value == Decimal("1.500000")
    assert len(calculations["operating_margin"].input_facts) == 2
