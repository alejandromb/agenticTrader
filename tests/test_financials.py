from __future__ import annotations

from decimal import Decimal

import pytest

from agentic_trading.financials import (
    extract_annual_financial_history,
    extract_annual_financial_snapshot,
    extract_available_annual_financial_snapshot,
    extract_available_quarterly_financial_snapshot,
    extract_quarterly_financial_history,
    infer_annual_period_start,
    require_filing_fact_coverage,
)


def _scoped_capex_facts(cik=1035267, accession="0001035267-26-000058"):
    return {
        "cik": cik,
        "facts": {
            "us-gaap": {
                "PaymentsToAcquireProductiveAssets": {
                    "label": "Productive assets",
                    "units": {
                        "USD": [
                            {
                                "start": "2026-01-01",
                                "end": "2026-06-30",
                                "val": 215900000,
                                "accn": accession,
                                "form": "10-Q",
                                "filed": "2026-07-21",
                                "fy": 2026,
                                "fp": "Q2",
                            }
                        ]
                    },
                }
            }
        },
    }


def test_verified_capex_mapping_preserves_provenance_and_ytd():
    facts = _scoped_capex_facts()
    # A standard tag can exist in company history but not the selected filing.
    facts["facts"]["us-gaap"]["PaymentsToAcquirePropertyPlantAndEquipment"] = {
        "label": "PP&E",
        "units": {
            "USD": [
                {
                    "start": "2025-01-01",
                    "end": "2025-06-30",
                    "val": 999,
                    "accn": "older-filing",
                    "form": "10-Q",
                    "filed": "2025-07-21",
                }
            ]
        },
    }
    snapshot, gaps = extract_available_quarterly_financial_snapshot(
        facts, accession_number="0001035267-26-000058", period_end="2026-06-30"
    )
    fact = snapshot["capital_expenditure"]
    assert fact.value == Decimal("215900000")
    assert fact.concept == "PaymentsToAcquireProductiveAssets"
    assert fact.period_start == "2026-01-01"
    assert not any("Missing capital_expenditure" in gap for gap in gaps)
    history = extract_quarterly_financial_history(
        facts, accession_number=fact.accession_number, through_period_end="2026-06-30"
    )
    assert history["capital_expenditure"] == (fact,)


@pytest.mark.parametrize(
    "cik,accession",
    [
        (123, "0001035267-26-000058"),
        (1035267, "0001035267-26-000099"),
    ],
)
def test_capex_mapping_does_not_leak_to_unreviewed_issuer_or_filing(cik, accession):
    snapshot, gaps = extract_available_quarterly_financial_snapshot(
        _scoped_capex_facts(cik, accession),
        accession_number=accession,
        period_end="2026-06-30",
    )
    assert "capital_expenditure" not in snapshot
    assert any("Missing capital_expenditure" in gap for gap in gaps)


def test_filing_coverage_distinguishes_unsupported_concepts_from_absence():
    facts = _scoped_capex_facts()
    require_filing_fact_coverage(facts, accession_number="0001035267-26-000058")
    with pytest.raises(ValueError, match="No older filing was substituted"):
        require_filing_fact_coverage(facts, accession_number="missing-accession")
    with pytest.raises(ValueError, match="no observations"):
        require_filing_fact_coverage({}, accession_number="missing-accession")


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
        "PaymentsToAcquireBusinessesNetOfCashAcquired": (53000000, True),
        "PaymentsOfDividends": (7507000000, True),
        "PaymentsForRepurchaseOfCommonStock": (8088000000, True),
        "ProceedsFromIssuanceOfLongTermDebt": (3983000000, True),
        "RepaymentsOfLongTermDebt": (2625000000, True),
        "NetCashProvidedByUsedInInvestingActivities": (-26350000000, True),
        "NetCashProvidedByUsedInFinancingActivities": (-13553000000, True),
        (
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"
            "PeriodIncreaseDecreaseIncludingExchangeRateEffect"
        ): (1785000000, True),
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
    assert snapshot["business_acquisitions"].value == Decimal("53000000")
    assert snapshot["dividends_paid"].value == Decimal("7507000000")
    assert snapshot["share_repurchases"].value == Decimal("8088000000")
    assert snapshot["long_term_debt_issued"].value == Decimal("3983000000")
    assert snapshot["long_term_debt_repaid"].value == Decimal("2625000000")
    assert snapshot["investing_cash_flow"].value == Decimal("-26350000000")
    assert snapshot["financing_cash_flow"].value == Decimal("-13553000000")
    assert snapshot["net_change_in_cash"].value == Decimal("1785000000")


def test_history_keeps_annual_comparatives_from_same_accession() -> None:
    accession = "0000320193-25-000079"
    observations = [
        {
            "start": "2024-09-29",
            "end": "2025-09-27",
            "val": 416161000000,
            "accn": accession,
            "fy": 2025,
            "fp": "FY",
            "form": "10-K",
            "filed": "2025-10-31",
        },
        {
            "start": "2023-10-01",
            "end": "2024-09-28",
            "val": 391035000000,
            "accn": accession,
            "fy": 2025,
            "fp": "FY",
            "form": "10-K",
            "filed": "2025-10-31",
        },
        {
            "start": "2025-06-29",
            "end": "2025-09-27",
            "val": 102000000000,
            "accn": accession,
            "fy": 2025,
            "fp": "FY",
            "form": "10-K",
            "filed": "2025-10-31",
        },
    ]
    facts = {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "label": "Revenue",
                    "units": {"USD": observations},
                }
            }
        }
    }

    history = extract_annual_financial_history(
        facts,
        accession_number=accession,
        through_period_end="2025-09-27",
    )

    assert [fact.value for fact in history["revenue"]] == [
        Decimal("391035000000"),
        Decimal("416161000000"),
    ]


def test_available_snapshot_uses_supported_dividend_alias() -> None:
    accession = "0000104169-26-000055"
    facts = {
        "facts": {
            "us-gaap": {
                "PaymentsOfDividendsCommonStock": {
                    "label": "Dividends paid",
                    "units": {
                        "USD": [
                            {
                                "start": "2025-02-01",
                                "end": "2026-01-31",
                                "val": 7507000000,
                                "accn": accession,
                                "fy": 2026,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2026-03-13",
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
        period_start="2025-02-01",
        period_end="2026-01-31",
    )

    assert snapshot["dividends_paid"].value == Decimal("7507000000")
    assert not any("dividends_paid" in gap for gap in gaps)


def test_quarterly_snapshot_separates_discrete_ytd_and_instant_contexts() -> None:
    accession = "0000320193-25-000050"

    def observation(start, end, value):
        item = {
            "end": end,
            "val": value,
            "accn": accession,
            "fy": 2025,
            "fp": "Q2",
            "form": "10-Q",
            "filed": "2025-07-31",
        }
        if start is not None:
            item["start"] = start
        return item

    facts = {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "label": "Revenue",
                    "units": {
                        "USD": [
                            observation("2024-04-01", "2024-06-29", 90),
                            observation("2025-03-31", "2025-06-28", 100),
                            observation("2024-12-30", "2025-06-28", 190),
                        ]
                    },
                },
                "NetCashProvidedByUsedInOperatingActivities": {
                    "label": "Operating cash flow",
                    "units": {
                        "USD": [
                            observation("2025-03-31", "2025-06-28", 20),
                            observation("2024-12-30", "2025-06-28", 45),
                        ]
                    },
                },
                "Assets": {
                    "label": "Assets",
                    "units": {"USD": [observation(None, "2025-06-28", 300)]},
                },
            }
        }
    }

    snapshot, gaps = extract_available_quarterly_financial_snapshot(
        facts, accession_number=accession, period_end="2025-06-28"
    )
    history = extract_quarterly_financial_history(
        facts, accession_number=accession, through_period_end="2025-06-28"
    )

    assert snapshot["revenue"].period_start == "2025-03-31"
    assert snapshot["revenue"].value == 100
    assert snapshot["operating_cash_flow"].period_start == "2024-12-30"
    assert snapshot["operating_cash_flow"].value == 45
    assert snapshot["assets"].period_start is None
    assert [fact.value for fact in history["revenue"]] == [90, 100]
    assert [fact.value for fact in history["operating_cash_flow"]] == [45]
    assert any("Missing net_income" in gap for gap in gaps)
