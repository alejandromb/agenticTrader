from __future__ import annotations

from decimal import Decimal

import pytest

from agentic_trading.xbrl import XbrlFactError, select_filing_fact


def company_facts(*observations: dict[str, object]) -> dict[str, object]:
    return {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "label": "Revenue",
                    "units": {"USD": list(observations)},
                }
            }
        }
    }


def observation(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "start": "2024-09-29",
        "end": "2025-09-27",
        "val": 416161000000,
        "accn": "0000320193-25-000079",
        "fy": 2025,
        "fp": "FY",
        "form": "10-K",
        "filed": "2025-10-31",
    }
    value.update(overrides)
    return value


def test_select_fact_by_exact_accession() -> None:
    facts = company_facts(
        observation(),
        observation(accn="0000320193-24-000123", val=391035000000),
    )

    fact = select_filing_fact(
        facts,
        taxonomy="us-gaap",
        concept="RevenueFromContractWithCustomerExcludingAssessedTax",
        unit="USD",
        accession_number="0000320193-25-000079",
    )

    assert fact.value == Decimal("416161000000")
    assert fact.fiscal_year == 2025
    assert fact.label == "Revenue"


def test_missing_fact_is_explicit() -> None:
    with pytest.raises(XbrlFactError, match="No us-gaap"):
        select_filing_fact(
            company_facts(observation()),
            taxonomy="us-gaap",
            concept="RevenueFromContractWithCustomerExcludingAssessedTax",
            unit="USD",
            accession_number="missing",
        )


def test_conflicting_observations_are_rejected() -> None:
    facts = company_facts(observation(), observation(val=1))

    with pytest.raises(XbrlFactError, match="Ambiguous"):
        select_filing_fact(
            facts,
            taxonomy="us-gaap",
            concept="RevenueFromContractWithCustomerExcludingAssessedTax",
            unit="USD",
            accession_number="0000320193-25-000079",
        )


def test_period_end_selects_current_year_from_comparatives() -> None:
    facts = company_facts(
        observation(),
        observation(start="2023-10-01", end="2024-09-28", val=391035000000),
    )

    fact = select_filing_fact(
        facts,
        taxonomy="us-gaap",
        concept="RevenueFromContractWithCustomerExcludingAssessedTax",
        unit="USD",
        accession_number="0000320193-25-000079",
        period_end="2025-09-27",
    )

    assert fact.value == Decimal("416161000000")
