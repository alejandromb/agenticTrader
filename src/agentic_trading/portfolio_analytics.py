"""Deterministic analytics for user-supplied hypothetical portfolios."""

from __future__ import annotations

import csv
import io
import json
import math
import re
import statistics
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import sessionmaker

from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.database import create_sqlite_engine
from agentic_trading.market_data import SqlitePriceDatasetRepository
from agentic_trading.models import PortfolioAnalysisArtifactModel

_TICKER = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


class PortfolioAnalysisError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Holding:
    ticker: str
    shares: Decimal


@dataclass(frozen=True, slots=True)
class PortfolioAnalysisArtifact:
    analysis_id: str
    dataset_id: str
    as_of: str
    valuation_date: str
    benchmark: str
    holdings_sha256: str
    holdings_storage_path: str
    holdings: tuple[Holding, ...]
    results: dict
    created_at: str


class SqlitePortfolioAnalyzer:
    def __init__(self, database_path: Path, artifact_root: Path) -> None:
        self._prices = SqlitePriceDatasetRepository(database_path, artifact_root)
        self._artifacts = LocalArtifactStore(artifact_root)
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )

    def analyze(
        self,
        holdings_path: Path,
        *,
        dataset_id: str,
        benchmark: str,
        as_of: str,
    ) -> PortfolioAnalysisArtifact:
        return self.analyze_bytes(
            holdings_path.read_bytes(),
            dataset_id=dataset_id,
            benchmark=benchmark,
            as_of=as_of,
        )

    def analyze_bytes(
        self,
        payload: bytes,
        *,
        dataset_id: str,
        benchmark: str,
        as_of: str,
    ) -> PortfolioAnalysisArtifact:
        """Analyze exact holdings CSV bytes without a temporary server file."""
        boundary = _date(as_of)
        benchmark = benchmark.strip().upper()
        if not _TICKER.fullmatch(benchmark):
            raise PortfolioAnalysisError("Invalid benchmark ticker")
        holdings = _parse_holdings(payload)
        holding_artifact = self._artifacts.put(payload)
        dataset = self._prices.get(dataset_id)
        observations = self._prices.observations(dataset_id)
        required = {item.ticker for item in holdings} | {benchmark}
        series: dict[str, dict[str, Decimal]] = {ticker: {} for ticker in required}
        for item in observations:
            if item.ticker in required and date.fromisoformat(item.date) <= boundary:
                series[item.ticker][item.date] = item.adjusted_close
        missing = sorted(ticker for ticker, values in series.items() if not values)
        if missing:
            tickers = ", ".join(missing)
            raise PortfolioAnalysisError(
                f"Dataset has no observations on or before as_of for: {tickers}"
            )
        common_dates = sorted(
            set.intersection(*(set(values) for values in series.values()))
        )
        if len(common_dates) < 3:
            raise PortfolioAnalysisError(
                "At least three common observations are required for risk metrics"
            )
        valuation_date = common_dates[-1]
        positions = []
        total_value = sum(
            holding.shares * series[holding.ticker][valuation_date]
            for holding in holdings
        )
        if total_value <= 0:
            raise PortfolioAnalysisError("Portfolio value must be positive")
        for holding in holdings:
            price = series[holding.ticker][valuation_date]
            market_value = holding.shares * price
            positions.append(
                {
                    "ticker": holding.ticker,
                    "shares": str(holding.shares),
                    "adjusted_close": str(price),
                    "market_value": str(market_value),
                    "weight": str(
                        (market_value / total_value).quantize(Decimal("0.000001"))
                    ),
                }
            )
        portfolio_values = [
            sum(holding.shares * series[holding.ticker][day] for holding in holdings)
            for day in common_dates
        ]
        benchmark_values = [series[benchmark][day] for day in common_dates]
        portfolio_returns = _returns(portfolio_values)
        benchmark_returns = _returns(benchmark_values)
        weights = [Decimal(item["weight"]) for item in positions]
        results = {
            "warning": (
                "Historical analytics are not forecasts or trade recommendations."
            ),
            "dataset_sha256": dataset.content_sha256,
            "adjustment_note": dataset.adjustment_note,
            "common_observations": len(common_dates),
            "positions": positions,
            "total_value": str(total_value),
            "portfolio_return": _number(portfolio_values[-1] / portfolio_values[0] - 1),
            "benchmark_return": _number(benchmark_values[-1] / benchmark_values[0] - 1),
            "annualized_volatility": _number(_annualized_volatility(portfolio_returns)),
            "benchmark_annualized_volatility": _number(
                _annualized_volatility(benchmark_returns)
            ),
            "tracking_error": _number(
                _annualized_volatility(
                    [
                        left - right
                        for left, right in zip(
                            portfolio_returns, benchmark_returns, strict=True
                        )
                    ]
                )
            ),
            "max_drawdown": _number(_max_drawdown(portfolio_values)),
            "max_weight": str(max(weights)),
            "concentration_hhi": str(sum(weight * weight for weight in weights)),
        }
        now = datetime.now(UTC).isoformat()
        model = PortfolioAnalysisArtifactModel(
            analysis_id=str(uuid4()),
            dataset_id=dataset_id,
            as_of=boundary.isoformat(),
            valuation_date=valuation_date,
            benchmark=benchmark,
            holdings_sha256=holding_artifact.sha256,
            holdings_storage_path=str(holding_artifact.path),
            holdings_json=json.dumps([_holding_payload(item) for item in holdings]),
            results_json=json.dumps(results, sort_keys=True),
            created_at=now,
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _from_model(model)

    def get(self, analysis_id: str) -> PortfolioAnalysisArtifact:
        with self._sessions() as session:
            model = session.get(PortfolioAnalysisArtifactModel, analysis_id)
            if model is None:
                raise PortfolioAnalysisError(
                    f"Portfolio analysis not found: {analysis_id}"
                )
            return _from_model(model)


def _parse_holdings(payload: bytes) -> tuple[Holding, ...]:
    try:
        reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig")))
    except UnicodeDecodeError as error:
        raise PortfolioAnalysisError("Holdings CSV must be UTF-8") from error
    required = {"ticker", "shares"}
    if reader.fieldnames is None or not set(reader.fieldnames) >= required:
        raise PortfolioAnalysisError("Holdings CSV requires ticker,shares columns")
    holdings = []
    seen = set()
    for line_number, row in enumerate(reader, start=2):
        ticker = (row.get("ticker") or "").strip().upper()
        if not _TICKER.fullmatch(ticker):
            raise PortfolioAnalysisError(f"Invalid ticker at line {line_number}")
        if ticker in seen:
            raise PortfolioAnalysisError(f"Duplicate holding at line {line_number}")
        try:
            shares = Decimal((row.get("shares") or "").strip())
        except InvalidOperation as error:
            raise PortfolioAnalysisError(
                f"Invalid shares at line {line_number}"
            ) from error
        if not shares.is_finite() or shares <= 0:
            raise PortfolioAnalysisError(
                f"Shares must be positive at line {line_number}"
            )
        seen.add(ticker)
        holdings.append(Holding(ticker, shares))
    if not holdings:
        raise PortfolioAnalysisError("Holdings CSV contains no positions")
    return tuple(sorted(holdings, key=lambda item: item.ticker))


def _returns(values: list[Decimal]) -> list[float]:
    return [
        float(current / prior - 1)
        for prior, current in zip(values, values[1:], strict=False)
    ]


def _annualized_volatility(returns: list[float]) -> float:
    if len(returns) < 2:
        raise PortfolioAnalysisError("At least two returns are required")
    return statistics.stdev(returns) * math.sqrt(252)


def _max_drawdown(values: list[Decimal]) -> Decimal:
    peak = values[0]
    maximum = Decimal(0)
    for value in values:
        peak = max(peak, value)
        maximum = min(maximum, value / peak - 1)
    return maximum


def _number(value: Decimal | float) -> str:
    return format(float(value), ".10f")


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise PortfolioAnalysisError(f"Invalid as_of date: {value}") from error


def _holding_payload(holding: Holding) -> dict[str, str]:
    return {"ticker": holding.ticker, "shares": str(holding.shares)}


def _from_model(model: PortfolioAnalysisArtifactModel) -> PortfolioAnalysisArtifact:
    return PortfolioAnalysisArtifact(
        analysis_id=model.analysis_id,
        dataset_id=model.dataset_id,
        as_of=model.as_of,
        valuation_date=model.valuation_date,
        benchmark=model.benchmark,
        holdings_sha256=model.holdings_sha256,
        holdings_storage_path=model.holdings_storage_path,
        holdings=tuple(
            Holding(ticker=item["ticker"], shares=Decimal(item["shares"]))
            for item in json.loads(model.holdings_json)
        ),
        results=json.loads(model.results_json),
        created_at=model.created_at,
    )
