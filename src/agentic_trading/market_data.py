"""Immutable import and retrieval of point-in-time adjusted-price datasets."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import PriceDatasetModel, PriceObservationModel

_TICKER = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")
_REQUIRED_COLUMNS = {"ticker", "date", "adjusted_close"}


class PriceDatasetError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PriceObservation:
    ticker: str
    date: str
    adjusted_close: Decimal


@dataclass(frozen=True, slots=True)
class PriceDataset:
    dataset_id: str
    source: str
    retrieved_at: str
    content_sha256: str
    storage_path: str
    adjustment_note: str
    row_count: int
    start_date: str
    end_date: str
    created_at: str


class SqlitePriceDatasetRepository:
    def __init__(self, database_path: Path, artifact_root: Path) -> None:
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )
        self._artifacts = LocalArtifactStore(artifact_root)

    def import_csv(
        self,
        path: Path,
        *,
        source: str,
        adjustment_note: str = "Adjusted-close values supplied by dataset source.",
    ) -> PriceDataset:
        return self.import_bytes(
            path.read_bytes(), source=source, adjustment_note=adjustment_note
        )

    def import_bytes(
        self,
        payload: bytes,
        *,
        source: str,
        adjustment_note: str = "Adjusted-close values supplied by dataset source.",
    ) -> PriceDataset:
        """Import exact CSV bytes without requiring a temporary server file."""
        if not source.strip():
            raise PriceDatasetError("Dataset source is required")
        observations = _parse_csv(payload)
        artifact = self._artifacts.put(payload)
        with self._sessions() as session:
            existing = session.scalar(
                select(PriceDatasetModel).where(
                    PriceDatasetModel.content_sha256 == artifact.sha256
                )
            )
            if existing is not None:
                return _dataset_from_model(existing)
        now = datetime.now(UTC).isoformat()
        model = PriceDatasetModel(
            dataset_id=str(uuid4()),
            source=source.strip(),
            retrieved_at=now,
            content_sha256=artifact.sha256,
            storage_path=str(artifact.path),
            adjustment_note=adjustment_note.strip(),
            row_count=len(observations),
            start_date=min(item.date for item in observations),
            end_date=max(item.date for item in observations),
            created_at=now,
        )
        with self._sessions.begin() as session:
            session.add(model)
            session.flush()
            session.add_all(
                PriceObservationModel(
                    dataset_id=model.dataset_id,
                    ticker=item.ticker,
                    date=item.date,
                    adjusted_close=str(item.adjusted_close),
                )
                for item in observations
            )
        return _dataset_from_model(model)

    def list_datasets(self) -> tuple[PriceDataset, ...]:
        with self._sessions() as session:
            models = session.scalars(
                select(PriceDatasetModel).order_by(
                    PriceDatasetModel.created_at.desc(),
                    PriceDatasetModel.dataset_id,
                )
            ).all()
            return tuple(_dataset_from_model(model) for model in models)

    def get(self, dataset_id: str) -> PriceDataset:
        with self._sessions() as session:
            model = session.get(PriceDatasetModel, dataset_id)
            if model is None:
                raise PriceDatasetError(f"Price dataset not found: {dataset_id}")
            return _dataset_from_model(model)

    def observations(self, dataset_id: str) -> tuple[PriceObservation, ...]:
        self.get(dataset_id)
        with self._sessions() as session:
            models = session.scalars(
                select(PriceObservationModel)
                .where(PriceObservationModel.dataset_id == dataset_id)
                .order_by(PriceObservationModel.ticker, PriceObservationModel.date)
            ).all()
            return tuple(
                PriceObservation(
                    ticker=model.ticker,
                    date=model.date,
                    adjusted_close=Decimal(model.adjusted_close),
                )
                for model in models
            )


def _parse_csv(payload: bytes) -> tuple[PriceObservation, ...]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise PriceDatasetError("Price CSV must be UTF-8") from error
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None or not set(reader.fieldnames) >= _REQUIRED_COLUMNS:
        raise PriceDatasetError("Price CSV requires ticker,date,adjusted_close columns")
    observations: list[PriceObservation] = []
    seen: set[tuple[str, str]] = set()
    last_date: dict[str, date] = {}
    for line_number, row in enumerate(reader, start=2):
        ticker = (row.get("ticker") or "").strip().upper()
        if not _TICKER.fullmatch(ticker):
            raise PriceDatasetError(f"Invalid ticker at line {line_number}")
        try:
            parsed_date = date.fromisoformat((row.get("date") or "").strip())
        except ValueError as error:
            raise PriceDatasetError(f"Invalid date at line {line_number}") from error
        previous = last_date.get(ticker)
        key = (ticker, parsed_date.isoformat())
        if key in seen:
            raise PriceDatasetError(f"Duplicate observation at line {line_number}")
        if previous is not None and parsed_date <= previous:
            raise PriceDatasetError(
                f"Dates must increase strictly for {ticker} at line {line_number}"
            )
        try:
            price = Decimal((row.get("adjusted_close") or "").strip())
        except InvalidOperation as error:
            raise PriceDatasetError(f"Invalid price at line {line_number}") from error
        if not price.is_finite() or price <= 0:
            raise PriceDatasetError(f"Price must be positive at line {line_number}")
        seen.add(key)
        last_date[ticker] = parsed_date
        observations.append(PriceObservation(ticker, key[1], price))
    if not observations:
        raise PriceDatasetError("Price CSV contains no observations")
    return tuple(observations)


def _dataset_from_model(model: PriceDatasetModel) -> PriceDataset:
    return PriceDataset(
        dataset_id=model.dataset_id,
        source=model.source,
        retrieved_at=model.retrieved_at,
        content_sha256=model.content_sha256,
        storage_path=model.storage_path,
        adjustment_note=model.adjustment_note,
        row_count=model.row_count,
        start_date=model.start_date,
        end_date=model.end_date,
        created_at=model.created_at,
    )
