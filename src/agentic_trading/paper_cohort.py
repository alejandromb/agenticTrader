"""Frozen prospective evaluation cohorts; no brokerage execution."""

import argparse
from decimal import Decimal
from pathlib import Path

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator

from agentic_trading.artifacts import LocalArtifactStore


class PaperCohort(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str = "1"
    registered_at: AwareDatetime
    entry_at: AwareDatetime
    selections: list[str] = Field(min_length=1)
    deferrals: list[str] = Field(min_length=1)
    benchmark: str = "SPY"
    horizons_days: list[int] = Field(default_factory=lambda: [30, 90])
    round_trip_cost_bps: Decimal = Field(ge=0, le=1000, allow_inf_nan=False)
    price_policy: str = Field(min_length=1)
    missing_policy: str = Field(min_length=1)
    selection_rule: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)

    @model_validator(mode="after")
    def prospective(self):
        if self.registered_at >= self.entry_at:
            raise ValueError("Registration must precede entry")
        symbols = self.selections + self.deferrals
        if len(set(symbols)) != len(symbols) or any(not s.strip() for s in symbols):
            raise ValueError("Symbols must be nonempty, unique and disjoint")
        if self.benchmark in symbols:
            raise ValueError("Benchmark must be separate from candidate cohorts")
        if not self.horizons_days or any(d <= 0 for d in self.horizons_days):
            raise ValueError("Positive evaluation horizons required")
        if len(set(self.horizons_days)) != len(self.horizons_days):
            raise ValueError("Duplicate evaluation horizon")
        return self


def equal_weight_return(
    entry: dict[str, Decimal],
    exit: dict[str, Decimal],
    symbols: list[str],
    cost_bps: Decimal,
) -> Decimal:
    """Complete-coverage price-ratio return; caller supplies aligned adjusted prices."""
    if not symbols or len(set(symbols)) != len(symbols):
        raise ValueError("Nonempty unique symbols required")
    if not cost_bps.is_finite() or not 0 <= cost_bps <= 1000:
        raise ValueError("Invalid cost assumption")
    returns = []
    for symbol in symbols:
        if symbol not in entry or symbol not in exit:
            raise ValueError("Incomplete price coverage; no survivor-only average")
        start, end = entry[symbol], exit[symbol]
        if not start.is_finite() or not end.is_finite() or start <= 0 or end < 0:
            raise ValueError("Invalid price")
        returns.append(end / start - 1)
    return sum(returns) / Decimal(len(returns)) - cost_bps / Decimal(10000)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--artifacts", type=Path, default=Path("data/paper"))
    args = parser.parse_args()
    plan = PaperCohort.model_validate_json(args.input.read_text())
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    if not plan.registered_at <= now < plan.entry_at:
        raise ValueError("Cannot register retrospectively or with a future timestamp")
    print(
        LocalArtifactStore(args.artifacts).put(plan.model_dump_json().encode()).sha256
    )


if __name__ == "__main__":
    main()
