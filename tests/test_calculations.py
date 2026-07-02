from decimal import Decimal

from agentic_trading.calculations import calculate_financial_history
from agentic_trading.xbrl import FilingFact


def fact(
    concept: str,
    value: str,
    end: str,
    start: str | None = "2024-01-01",
    *,
    form: str = "10-K",
    fiscal_period: str = "FY",
):
    return FilingFact(
        taxonomy="us-gaap",
        concept=concept,
        label=concept,
        unit="USD",
        value=Decimal(value),
        period_start=start,
        period_end=end,
        filed="2026-01-01",
        form=form,
        accession_number="accession",
        fiscal_year=2025,
        fiscal_period=fiscal_period,
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


def test_quarterly_calculations_reject_incompatible_duration_contexts() -> None:
    revenue_quarter = fact(
        "Revenue",
        "100",
        "2025-06-28",
        start="2025-03-31",
        form="10-Q",
        fiscal_period="Q2",
    )
    operating_income_ytd = fact(
        "OperatingIncome",
        "20",
        "2025-06-28",
        start="2024-12-30",
        form="10-Q",
        fiscal_period="Q2",
    )
    operating_cash_ytd = fact(
        "OperatingCashFlow",
        "45",
        "2025-06-28",
        start="2024-12-30",
        form="10-Q",
        fiscal_period="Q2",
    )
    capex_quarter = fact(
        "CapitalExpenditure",
        "10",
        "2025-06-28",
        start="2025-03-31",
        form="10-Q",
        fiscal_period="Q2",
    )

    assert (
        calculate_financial_history(
            {
                    "revenue": (revenue_quarter,),
                "operating_income": (operating_income_ytd,),
                "operating_cash_flow": (operating_cash_ytd,),
                "capital_expenditure": (capex_quarter,),
            }
        )
        == ()
    )
