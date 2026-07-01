"""Deterministic as-of screening over persisted research calculations."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import (
    CandidateClaimModel,
    InvestmentMemoArtifactModel,
    ResearchRunModel,
    ResearchScreenArtifactModel,
)

SUPPORTED_METRICS = (
    "revenue_growth",
    "operating_margin",
    "net_margin",
    "current_ratio",
    "free_cash_flow_approximation",
)


@dataclass(frozen=True, slots=True)
class ScreenFilters:
    min_revenue_growth: Decimal | None = None
    min_operating_margin: Decimal | None = None
    min_net_margin: Decimal | None = None
    min_current_ratio: Decimal | None = None
    min_free_cash_flow: Decimal | None = None


@dataclass(frozen=True, slots=True)
class ScreenResult:
    ticker: str
    run_id: str
    run_as_of: str
    metrics: dict[str, str]


@dataclass(frozen=True, slots=True)
class ResearchScreenArtifact:
    screen_id: str
    as_of: str
    filters: ScreenFilters
    results: tuple[ScreenResult, ...]
    created_at: str


class SqliteResearchScreener:
    def __init__(self, database_path: Path) -> None:
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )

    def screen(self, *, as_of: str, filters: ScreenFilters) -> ResearchScreenArtifact:
        boundary = _datetime(as_of)
        with self._sessions() as session:
            rows = session.execute(
                select(ResearchRunModel, InvestmentMemoArtifactModel)
                .join(
                    InvestmentMemoArtifactModel,
                    InvestmentMemoArtifactModel.run_id == ResearchRunModel.run_id,
                )
                .order_by(
                    ResearchRunModel.as_of.desc(), ResearchRunModel.created_at.desc()
                )
            ).all()
            latest_by_ticker: dict[str, tuple[ResearchRunModel, str]] = {}
            for run, memo_model in rows:
                if _datetime(run.as_of) > boundary:
                    continue
                ticker = json.loads(memo_model.content_json)["subject"]["ticker"]
                latest_by_ticker.setdefault(ticker, (run, memo_model.content_json))

            results: list[ScreenResult] = []
            for ticker, (run, _) in latest_by_ticker.items():
                claims = session.scalars(
                    select(CandidateClaimModel).where(
                        CandidateClaimModel.run_id == run.run_id,
                        CandidateClaimModel.taxonomy == "agentic-trading",
                        CandidateClaimModel.concept.in_(SUPPORTED_METRICS),
                    )
                ).all()
                latest: dict[str, CandidateClaimModel] = {}
                for claim in claims:
                    current = latest.get(claim.concept)
                    if current is None or claim.period_end > current.period_end:
                        latest[claim.concept] = claim
                values = {
                    name: Decimal(claim.numeric_value)
                    for name, claim in latest.items()
                    if claim.numeric_value is not None
                }
                if _passes(values, filters):
                    results.append(
                        ScreenResult(
                            ticker=ticker,
                            run_id=run.run_id,
                            run_as_of=run.as_of,
                            metrics={
                                name: str(value) for name, value in values.items()
                            },
                        )
                    )
        results.sort(
            key=lambda item: (
                -Decimal(item.metrics.get("revenue_growth", "-Infinity")),
                item.ticker,
            )
        )
        now = datetime.now(UTC).isoformat()
        model = ResearchScreenArtifactModel(
            screen_id=str(uuid4()),
            as_of=boundary.isoformat(),
            filters_json=json.dumps(_filter_payload(filters), sort_keys=True),
            results_json=json.dumps([asdict(item) for item in results], sort_keys=True),
            created_at=now,
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _artifact_from_model(model)

    def get(self, screen_id: str) -> ResearchScreenArtifact:
        with self._sessions() as session:
            model = session.get(ResearchScreenArtifactModel, screen_id)
            if model is None:
                raise ValueError(f"Research screen not found: {screen_id}")
            return _artifact_from_model(model)


def _passes(values: dict[str, Decimal], filters: ScreenFilters) -> bool:
    requirements = {
        "revenue_growth": filters.min_revenue_growth,
        "operating_margin": filters.min_operating_margin,
        "net_margin": filters.min_net_margin,
        "current_ratio": filters.min_current_ratio,
        "free_cash_flow_approximation": filters.min_free_cash_flow,
    }
    return all(
        minimum is None or (metric in values and values[metric] >= minimum)
        for metric, minimum in requirements.items()
    )


def _datetime(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"Invalid as_of timestamp: {value}") from error
    if parsed.tzinfo is None:
        raise ValueError("as_of timestamp must include a timezone")
    return parsed


def _filter_payload(filters: ScreenFilters) -> dict[str, str | None]:
    return {
        key: str(value) if value is not None else None
        for key, value in asdict(filters).items()
    }


def _artifact_from_model(model: ResearchScreenArtifactModel) -> ResearchScreenArtifact:
    filter_values = json.loads(model.filters_json)
    filters = ScreenFilters(
        **{
            key: Decimal(value) if value is not None else None
            for key, value in filter_values.items()
        }
    )
    return ResearchScreenArtifact(
        screen_id=model.screen_id,
        as_of=model.as_of,
        filters=filters,
        results=tuple(ScreenResult(**item) for item in json.loads(model.results_json)),
        created_at=model.created_at,
    )
