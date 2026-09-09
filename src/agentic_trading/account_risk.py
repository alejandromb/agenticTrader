"""Manual, auditable account loss reviews. Never produces broker orders."""

import argparse
import json
from decimal import Decimal
from pathlib import Path
from typing import Annotated
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.portfolio_snapshots import Money, Observation


class RiskPolicy(Observation):
    account_ref: UUID
    baseline_at: AwareDatetime
    baseline_value: Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
    warning_loss: Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
    review_loss: Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
    max_age_seconds: int = Field(default=900, gt=0)

    @model_validator(mode="after")
    def ordered_thresholds(self):
        if self.review_loss <= self.warning_loss:
            raise ValueError("Review loss must exceed warning loss")
        return self


class CashFlow(Observation):
    event_id: str = Field(min_length=1)
    occurred_at: AwareDatetime
    amount: Money  # External deposits positive; withdrawals negative. Not trades.


class RiskCheck(Observation):
    policy: RiskPolicy
    account_ref: UUID
    observed_at: (
        AwareDatetime  # Retrieval time, never presented as broker valuation time.
    )
    source_at: AwareDatetime | None = None
    evaluated_at: AwareDatetime
    account_value: Money
    flows_verified_through: AwareDatetime | None = None
    cash_flows: tuple[CashFlow, ...] = ()

    @model_validator(mode="after")
    def consistent_context(self):
        if self.account_ref != self.policy.account_ref:
            raise ValueError("Account must match policy")
        if not self.policy.baseline_at <= self.observed_at <= self.evaluated_at:
            raise ValueError("Require baseline <= observation <= evaluation")
        if self.source_at is not None and not (
            self.policy.baseline_at <= self.source_at <= self.observed_at
        ):
            raise ValueError("Source time must be between baseline and retrieval")
        if self.flows_verified_through is not None and not (
            self.policy.baseline_at <= self.flows_verified_through <= self.observed_at
        ):
            raise ValueError("Invalid flow verification time")
        if len({flow.event_id for flow in self.cash_flows}) != len(self.cash_flows):
            raise ValueError("Duplicate external cash flow")
        cutoff = self.source_at or self.observed_at
        if any(
            not self.policy.baseline_at < f.occurred_at <= cutoff
            for f in self.cash_flows
        ):
            raise ValueError("Cash flow outside baseline-to-valuation interval")
        return self


def evaluate(check: RiskCheck) -> dict:
    """Fixed-baseline dollar change, not a time-weighted return or trailing stop."""
    check = RiskCheck.model_validate_json(check.model_dump_json())
    flows = sum((f.amount for f in check.cash_flows), Decimal(0))
    change = check.account_value - check.policy.baseline_value - flows
    observed_level = (
        "review"
        if change <= -check.policy.review_loss
        else "warning"
        if change <= -check.policy.warning_loss
        else "below_threshold"
    )
    reasons = []
    if check.source_at is None:
        reasons.append("Broker valuation timestamp unavailable")
    elif (check.evaluated_at - check.source_at).total_seconds() > (
        check.policy.max_age_seconds
    ):
        reasons.append("Broker valuation is stale")
    cutoff = check.source_at or check.observed_at
    if check.flows_verified_through is None or check.flows_verified_through < cutoff:
        reasons.append("External cash-flow history is not verified through valuation")
    return {
        "schema_version": "1.0",
        "status": "needs_data" if reasons else observed_level,
        "provisional_level": observed_level if reasons else None,
        "cash_flow_adjusted_change": str(change),
        "net_external_flows": str(flows),
        "warning_account_value": str(
            check.policy.baseline_value + flows - check.policy.warning_loss
        ),
        "review_account_value": str(
            check.policy.baseline_value + flows - check.policy.review_loss
        ),
        "limitations": reasons
        + [
            "Manual review only; no orders, notifications or recurring monitoring",
            "Dollar change is not a cash-flow-adjusted percentage return",
            "Thresholds are not guaranteed loss caps; no automatic liquidation",
        ],
    }


def save_check(check: RiskCheck, root: Path) -> tuple[str, dict]:
    result = evaluate(check)
    envelope = {"input": check.model_dump(mode="json"), "result": result}
    artifact = LocalArtifactStore(root).put(
        json.dumps(envelope, sort_keys=True).encode()
    )
    return artifact.sha256, result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    check = RiskCheck.model_validate_json(args.input.read_text())
    digest, result = save_check(check, args.artifact_root)
    print(json.dumps({"artifact_sha256": digest, **result}, sort_keys=True))


if __name__ == "__main__":
    main()
