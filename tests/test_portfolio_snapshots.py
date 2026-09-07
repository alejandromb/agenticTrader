from uuid import uuid4

import pytest
from pydantic import ValidationError

from agentic_trading.migrations import upgrade_database
from agentic_trading.portfolio_snapshots import (
    Holding,
    PortfolioObservation,
    PortfolioSnapshotRepository,
)


def observation(**changes):
    return PortfolioObservation.model_validate(
        dict(
            account_ref=uuid4(),
            provider="synthetic",
            positions_complete=True,
            holdings=[dict(symbol="AAA", quantity="10", quote="20")],
            **changes,
        )
    )


def test_restart_history_account_isolation_and_incomplete_refresh(tmp_path):
    db = tmp_path / "state.db"
    upgrade_database(db)
    repo = PortfolioSnapshotRepository(db, tmp_path / "artifacts")
    value = observation()
    first = repo.save(value)
    second = repo.save(value)
    assert first.snapshot_id != second.snapshot_id
    assert first.content_sha256 == second.content_sha256
    incomplete = value.model_copy(update={"positions_complete": False})
    repo.save(incomplete)
    restarted = PortfolioSnapshotRepository(db, tmp_path / "artifacts")
    assert restarted.get(value.account_ref, first.snapshot_id) == first
    assert restarted.latest_complete(value.account_ref) == second
    assert restarted.latest_complete(uuid4()) is None
    with pytest.raises(LookupError):
        restarted.get(uuid4(), first.snapshot_id)


@pytest.mark.parametrize(
    "field,value",
    [
        ("account_ref", "123456789"),
        ("currency", "EUR"),
        ("cash", "NaN"),
        ("buying_power", "Infinity"),
        ("source_at", "2026-09-07T00:00:00"),
        ("token", "secret-sentinel"),
    ],
)
def test_invalid_observations_rejected(field, value):
    payload = observation().model_dump()
    payload[field] = value
    with pytest.raises(ValidationError):
        PortfolioObservation.model_validate(payload)


def test_missing_values_stay_unknown_and_duplicates_rejected():
    value = observation()
    assert value.cash is None
    assert value.holdings[0].average_cost is None
    assert "Some average costs are unavailable." in value.limitations
    payload = value.model_dump()
    payload["holdings"] *= 2
    with pytest.raises(ValidationError):
        PortfolioObservation.model_validate(payload)
    with pytest.raises(ValidationError):
        Holding(symbol="AAA", quantity="-1")


def test_artifact_tampering_is_detected(tmp_path):
    db = tmp_path / "state.db"
    upgrade_database(db)
    root = tmp_path / "artifacts"
    repo = PortfolioSnapshotRepository(db, root)
    saved = repo.save(observation())
    path = root / "sha256" / saved.content_sha256[:2] / saved.content_sha256
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        repo.get(saved.observation.account_ref, saved.snapshot_id)
