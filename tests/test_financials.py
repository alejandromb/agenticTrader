from __future__ import annotations

from decimal import Decimal

from agentic_trading.financials import (
    extract_annual_financial_snapshot,
    extract_available_annual_financial_snapshot,
    infer_annual_period_start,
)


def test_extract_minimum_annual_financial_snapshot() -> None:
    accession = "0000320193-25-000079"
    facts = {"facts": {"us-gaap": {}}}
    values = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": 416161000000,
        "NetIncomeLoss": 112010000000,
        "Assets": 359241000000,
        "Liabilities": 285508000000,
        "NetCashProvidedByUsedInOperatingActivities": 111482000000,
    }
    instant = {"Assets", "Liabilities"}
    for concept, value in values.items():
        observation = {
            "end": "2025-09-27",
            "val": value,
            "accn": accession,
            "fy": 2025,
            "fp": "FY",
            "form": "10-K",
            "filed": "2025-10-31",
        }
        if concept not in instant:
            observation["start"] = "2024-09-29"
        facts["facts"]["us-gaap"][concept] = {
            "label": concept,
            "units": {"USD": [observation]},
        }

    snapshot = extract_annual_financial_snapshot(
        facts,
        accession_number=accession,
        period_start="2024-09-29",
        period_end="2025-09-27",
    )

    assert snapshot["revenue"].value == Decimal("416161000000")
    assert snapshot["net_income"].value == Decimal("112010000000")
    assert snapshot["assets"].period_start is None
    assert snapshot["operating_cash_flow"].value == Decimal("111482000000")
    assert (
        infer_annual_period_start(
            facts,
            accession_number=accession,
            period_end="2025-09-27",
        )
        == "2024-09-29"
    )


def test_available_snapshot_reports_missing_issuer_concept() -> None:
    accession = "0000320193-25-000079"
    facts = {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "label": "Revenue",
                    "units": {
                        "USD": [
                            {
                                "start": "2024-09-29",
                                "end": "2025-09-27",
                                "val": 416161000000,
                                "accn": accession,
                                "fy": 2025,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2025-10-31",
                            }
                        ]
                    },
                }
            }
        }
    }

    snapshot, gaps = extract_available_annual_financial_snapshot(
        facts,
        accession_number=accession,
        period_start="2024-09-29",
        period_end="2025-09-27",
    )

    assert set(snapshot) == {"revenue"}
    assert "Missing liabilities (us-gaap:Liabilities)" in gaps
    assert (
        "Missing capital_expenditure "
        "(us-gaap:PaymentsToAcquirePropertyPlantAndEquipment)"
    ) in gaps


def test_available_snapshot_extracts_optional_liquidity_and_profit_metrics() -> None:
    accession = "0000320193-25-000079"
    concepts = {
        "RevenueFromContractWithCustomerExcludingAssessedTax": (
            416161000000,
            True,
        ),
        "CashAndCashEquivalentsAtCarryingValue": (35934000000, False),
        "AssetsCurrent": (147957000000, False),
        "LiabilitiesCurrent": (165631000000, False),
        "OperatingIncomeLoss": (133050000000, True),
        "PaymentsToAcquirePropertyPlantAndEquipment": (12715000000, True),
        "LongTermDebtCurrent": (12350000000, False),
        "LongTermDebtNoncurrent": (78328000000, False),
    }
    facts: dict[str, object] = {"facts": {"us-gaap": {}}}
    for concept, (value, duration) in concepts.items():
        observation: dict[str, object] = {
            "end": "2025-09-27",
            "val": value,
            "accn": accession,
            "fy": 2025,
            "fp": "FY",
            "form": "10-K",
            "filed": "2025-10-31",
        }
        if duration:
            observation["start"] = "2024-09-29"
        facts["facts"]["us-gaap"][concept] = {
            "label": concept,
            "units": {"USD": [observation]},
        }

    snapshot, _ = extract_available_annual_financial_snapshot(
        facts,
        accession_number=accession,
        period_start="2024-09-29",
        period_end="2025-09-27",
    )

    assert snapshot["cash_and_cash_equivalents"].value == Decimal("35934000000")
    assert snapshot["operating_income"].value == Decimal("133050000000")
    assert snapshot["capital_expenditure"].value == Decimal("12715000000")
