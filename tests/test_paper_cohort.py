from decimal import Decimal as D

import pytest

from agentic_trading.paper_cohort import PaperCohort, equal_weight_return


def plan(**changes):
    return PaperCohort(
        **(
            dict(
                registered_at="2026-09-10T12:00:00Z",
                entry_at="2026-09-11T20:00:00Z",
                selections=["AAA"],
                deferrals=["BBB"],
                round_trip_cost_bps="10",
                price_policy="Same-date adjusted close",
                missing_policy="Incomplete result",
                selection_rule="Pilot",
                source_ref="fixture",
            )
            | changes
        )
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"entry_at": "2026-09-09T12:00:00Z"},
        {"deferrals": ["AAA"]},
        {"horizons_days": [0]},
        {"selections": ["SPY"]},
    ],
)
def test_invalid_cohort(changes):
    with pytest.raises(ValueError):
        plan(**changes)


def test_return_and_explicit_total_loss():
    assert equal_weight_return(
        {"A": D(100), "B": D(100)}, {"A": D(110), "B": D(0)}, ["A", "B"], D(10)
    ) == D("-0.451")


def test_no_survivor_only_result():
    with pytest.raises(ValueError):
        equal_weight_return({"A": D(100)}, {}, ["A"], D(0))
