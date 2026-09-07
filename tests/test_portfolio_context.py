from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from agentic_trading.migrations import upgrade_database
from agentic_trading.portfolio_context import equity_context
from agentic_trading.portfolio_snapshots import (
    PortfolioObservation,
    PortfolioSnapshotRepository,
    RefreshRecord,
)


def sample(**changes):
    payload = dict(
        account_ref=uuid4(),
        provider="synthetic",
        account_value="500",
        cash="100",
        positions_complete=True,
        holdings=[
            dict(symbol="AAA", quantity="10", quote="20", average_cost="15"),
            dict(symbol="BBB", quantity="5", quote="40"),
        ],
    )
    payload.update(changes)
    return PortfolioObservation.model_validate(payload)


def test_contract_formula_fixture():
    result = equity_context(sample())
    assert Decimal(result["equity_weight_denominator"]) == 400
    for row in result["holdings"]:
        assert Decimal(row["position_value"]) == 200
        assert Decimal(row["equity_weight"]) == Decimal("0.5")
        assert Decimal(row["account_weight"]) == Decimal("0.4")
    assert Decimal(result["holdings"][0]["estimated_unrealized_result"]) == 50
    assert result["holdings"][1]["estimated_unrealized_result"] is None


@pytest.mark.parametrize(
    "holdings,complete",
    [
        ([dict(symbol="AAA", quantity="10")], True),
        ([dict(symbol="AAA", quantity="10", quote="20")], False),
        ([dict(symbol="AAA", quantity="0", quote="20")], True),
        ([dict(symbol="AAA", quantity="-10", quote="20", position_type="short")], True),
        ([dict(symbol="AAA", quantity="10", quote="20", position_type="boxed")], True),
    ],
)
def test_weights_not_fabricated(holdings, complete):
    result = equity_context(sample(holdings=holdings, positions_complete=complete))
    assert result["equity_weight_denominator"] is None
    assert all(row["equity_weight"] is None for row in result["holdings"])


def test_refresh_history_is_durable_and_account_scoped(tmp_path):
    db, root = tmp_path / "db", tmp_path / "artifacts"
    upgrade_database(db)
    repo = PortfolioSnapshotRepository(db, root)
    value = sample()
    saved = repo.save(value)
    now = datetime.now(UTC)
    success = RefreshRecord(
        account_ref=value.account_ref,
        started_at=now,
        ended_at=now,
        snapshot_id=saved.snapshot_id,
    )
    repo.record_refresh(success)
    failed = RefreshRecord(
        account_ref=value.account_ref,
        started_at=now,
        ended_at=now + timedelta(seconds=1),
        failure="disconnected",
    )
    repo.record_refresh(failed)
    restarted = PortfolioSnapshotRepository(db, root)
    assert restarted.refresh_history(value.account_ref) == (failed, success)
    assert restarted.refresh_history(uuid4()) == ()
    assert restarted.latest_complete(value.account_ref) == saved
    with pytest.raises(LookupError):
        repo.record_refresh(success.model_copy(update={"account_ref": uuid4()}))
    with pytest.raises(ValidationError):
        RefreshRecord(
            account_ref=value.account_ref,
            started_at=now,
            ended_at=now,
            failure="raw exception with secret",
        )
    with pytest.raises(ValidationError):
        RefreshRecord(
            account_ref=value.account_ref,
            started_at=now,
            ended_at=now - timedelta(seconds=1),
            failure="disconnected",
        )


def test_equivalent_decimal_and_time_inputs_share_hash(tmp_path):
    db, root = tmp_path / "db", tmp_path / "artifacts"
    upgrade_database(db)
    repo = PortfolioSnapshotRepository(db, root)
    first = sample(source_at="2026-09-07T12:00:00Z")
    payload = first.model_dump(mode="json")
    payload["account_value"] = "500.000"
    payload["source_at"] = "2026-09-07T08:00:00-04:00"
    payload["holdings"].reverse()
    assert (
        repo.save(first).content_sha256
        == repo.save(PortfolioObservation.model_validate(payload)).content_sha256
    )


def test_mixed_quote_times_are_visible():
    value = sample(
        holdings=[
            dict(
                symbol="AAA", quantity="1", quote="20", quote_at="2026-09-04T20:00:00Z"
            ),
            dict(
                symbol="BBB", quantity="1", quote="40", quote_at="2026-09-04T19:59:00Z"
            ),
        ]
    )
    assert (
        "Quotes have different observation times."
        in equity_context(value)["limitations"]
    )
