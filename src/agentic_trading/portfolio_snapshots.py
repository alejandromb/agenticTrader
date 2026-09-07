"""Validated private portfolio observations and append-only snapshot storage."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import PortfolioSnapshotModel

Money = Annotated[Decimal, Field(allow_inf_nan=False)]


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Holding(Observation):
    symbol: str = Field(pattern=r"^[A-Z][A-Z0-9.-]{0,9}$")
    quantity: Money
    position_type: Literal["long", "short", "boxed", "empty"] = "long"
    average_cost: Annotated[Decimal, Field(ge=0, allow_inf_nan=False)] | None = None
    quote: Annotated[Decimal, Field(ge=0, allow_inf_nan=False)] | None = None
    quote_at: AwareDatetime | None = None

    @model_validator(mode="after")
    def validate_position(self):
        if self.position_type == "long" and self.quantity < 0:
            raise ValueError("Long quantity cannot be negative")
        if self.position_type == "short" and self.quantity > 0:
            raise ValueError("Short quantity cannot be positive")
        if self.position_type == "empty" and self.quantity != 0:
            raise ValueError("Empty position must have zero quantity")
        return self


class PortfolioObservation(Observation):
    schema_version: Literal["1.0"] = "1.0"
    account_ref: UUID  # Local opaque reference, never a brokerage account number.
    provider: Literal["robinhood", "synthetic"]
    currency: Literal["USD"] = "USD"
    source_at: AwareDatetime | None = None
    account_value: Money | None = None
    cash: Money | None = None
    buying_power: Money | None = None
    unleveraged_buying_power: Money | None = None
    pending_deposits: Money | None = None
    equity_value: Money | None = None
    other_asset_value: Money | None = None
    positions_complete: bool
    holdings: tuple[Holding, ...]

    @model_validator(mode="after")
    def validate_symbols(self):
        if len({h.symbol for h in self.holdings}) != len(self.holdings):
            raise ValueError("Duplicate holding symbols")
        return self

    @property
    def limitations(self) -> tuple[str, ...]:
        gaps = []
        if not self.positions_complete:
            gaps.append("Equity position collection is incomplete.")
        if any(h.quote is None for h in self.holdings):
            gaps.append("Some equity quotes are unavailable.")
        if any(h.average_cost is None for h in self.holdings):
            gaps.append("Some average costs are unavailable.")
        if self.source_at is None:
            gaps.append("Broker source timestamp is unavailable.")
        if any(h.quote_at is None for h in self.holdings):
            gaps.append("Some quote timestamps are unavailable.")
        if any(h.position_type not in ("long", "empty") for h in self.holdings):
            gaps.append("Short or boxed concentration calculations are unsupported.")
        if self.other_asset_value is None or self.other_asset_value != 0:
            gaps.append("Equity detail does not establish complete account holdings.")
        gaps.append("Margin debt and maintenance requirements are unavailable.")
        return tuple(gaps)

    @property
    def coverage(self) -> str:
        return (
            "complete"
            if self.positions_complete
            and all(h.quote is not None for h in self.holdings)
            else "incomplete"
        )


class SavedSnapshot(Observation):
    snapshot_id: UUID
    collected_at: AwareDatetime
    content_sha256: str
    observation: PortfolioObservation


class PortfolioSnapshotRepository:
    def __init__(self, database_path: Path, artifact_root: Path):
        self._sessions = sessionmaker(create_sqlite_engine(database_path))
        self._artifacts = LocalArtifactStore(artifact_root)

    def save(self, observation: PortfolioObservation) -> SavedSnapshot:
        # Roundtrip revalidates even models built using Pydantic's unsafe helpers.
        observation = PortfolioObservation.model_validate_json(
            observation.model_dump_json()
        )
        observation = observation.model_copy(
            update={
                "holdings": tuple(sorted(observation.holdings, key=lambda h: h.symbol))
            }
        )
        artifact = self._artifacts.put(observation.model_dump_json().encode())
        snapshot_id = uuid4()
        collected_at = datetime.now(UTC)
        with self._sessions.begin() as session:
            session.add(
                PortfolioSnapshotModel(
                    snapshot_id=str(snapshot_id),
                    account_ref=str(observation.account_ref),
                    collected_at=collected_at.isoformat(),
                    content_sha256=artifact.sha256,
                    coverage=observation.coverage,
                )
            )
        return SavedSnapshot(
            snapshot_id=snapshot_id,
            collected_at=collected_at,
            content_sha256=artifact.sha256,
            observation=observation,
        )

    def get(self, account_ref: UUID, snapshot_id: UUID) -> SavedSnapshot:
        with self._sessions() as session:
            row = session.get(PortfolioSnapshotModel, str(snapshot_id))
            if row is None or row.account_ref != str(account_ref):
                raise LookupError("Snapshot not found for this account")
            observation = PortfolioObservation.model_validate_json(
                self._artifacts.get(row.content_sha256)
            )
            if str(observation.account_ref) != row.account_ref:
                raise ValueError("Snapshot account integrity mismatch")
            return SavedSnapshot(
                snapshot_id=row.snapshot_id,
                collected_at=row.collected_at,
                content_sha256=row.content_sha256,
                observation=observation,
            )

    def latest_complete(self, account_ref: UUID) -> SavedSnapshot | None:
        with self._sessions() as session:
            row = session.scalar(
                select(PortfolioSnapshotModel)
                .where(
                    PortfolioSnapshotModel.account_ref == str(account_ref),
                    PortfolioSnapshotModel.coverage == "complete",
                )
                .order_by(
                    PortfolioSnapshotModel.collected_at.desc(),
                    PortfolioSnapshotModel.snapshot_id.desc(),
                )
                .limit(1)
            )
            return None if row is None else self.get(account_ref, UUID(row.snapshot_id))
