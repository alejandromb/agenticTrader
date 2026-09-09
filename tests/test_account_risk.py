import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from agentic_trading.account_risk import RiskCheck, evaluate, save_check
from agentic_trading.artifacts import LocalArtifactStore

ACCOUNT = UUID("00000000-0000-0000-0000-000000000001")
NOW = datetime(2026, 9, 9, 20, tzinfo=UTC)


def sample(**updates):
    data = dict(
        policy=dict(
            account_ref=ACCOUNT,
            baseline_at=NOW - timedelta(days=1),
            baseline_value="1000",
            warning_loss="100",
            review_loss="150",
        ),
        account_ref=ACCOUNT,
        observed_at=NOW,
        source_at=NOW,
        evaluated_at=NOW,
        account_value="1000",
        flows_verified_through=NOW,
    )
    data.update(updates)
    return RiskCheck.model_validate(data)


@pytest.mark.parametrize(
    "value,status",
    [
        ("1000", "below_threshold"),
        ("900.01", "below_threshold"),
        ("900", "warning"),
        ("850.01", "warning"),
        ("850", "review"),
        ("-10", "review"),
    ],
)
def test_threshold_boundaries(value, status):
    assert evaluate(sample(account_value=value))["status"] == status


@pytest.mark.parametrize("amount,value", [("500", "1400"), ("-200", "700")])
def test_external_flows_do_not_mask_or_create_loss(amount, value):
    result = evaluate(
        sample(
            account_value=value,
            cash_flows=[
                dict(
                    event_id="transfer-1",
                    amount=amount,
                    occurred_at=NOW - timedelta(hours=1),
                )
            ],
        )
    )
    assert Decimal(result["cash_flow_adjusted_change"]) == -100
    assert result["status"] == "warning"


@pytest.mark.parametrize(
    "updates",
    [
        {"source_at": None},
        {"flows_verified_through": None},
        {"source_at": NOW - timedelta(seconds=901)},
        {"flows_verified_through": NOW - timedelta(seconds=1)},
    ],
)
def test_incomplete_or_stale_data_never_reports_clear(updates):
    result = evaluate(sample(**updates))
    assert result["status"] == "needs_data"
    assert result["provisional_level"] == "below_threshold"


@pytest.mark.parametrize(
    "updates",
    [
        {"account_ref": UUID(int=2)},
        {"account_value": "NaN"},
        {"account_value": "Infinity"},
        {"observed_at": NOW + timedelta(seconds=1)},
        {"source_at": NOW + timedelta(seconds=1)},
        {"evaluated_at": "2026-09-09T20:00:00"},
    ],
)
def test_invalid_inputs_fail(updates):
    with pytest.raises(ValidationError):
        sample(**updates)


def test_duplicate_flows_rejected():
    flow = dict(event_id="same", amount="10", occurred_at=NOW)
    with pytest.raises(ValidationError, match="Duplicate"):
        sample(cash_flows=[flow, flow])


def test_artifact_round_trip_is_repeatable(tmp_path):
    check = sample(account_value="850")
    digest, result = save_check(check, tmp_path)
    assert save_check(check, tmp_path) == (digest, result)
    envelope = json.loads(LocalArtifactStore(tmp_path).get(digest))
    assert evaluate(RiskCheck.model_validate(envelope["input"])) == result
