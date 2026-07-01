"""Deterministic, cost-aware historical simulation without order generation."""

from __future__ import annotations

import json
import math
import re
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.market_data import SqlitePriceDatasetRepository
from agentic_trading.models import BacktestArtifactModel

STRATEGY = "moving-average"
STRATEGY_VERSION = "1.0"
_TICKER = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


class BacktestError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class BacktestArtifact:
    backtest_id: str
    dataset_id: str
    ticker: str
    benchmark: str
    strategy: str
    strategy_version: str
    parameters: dict
    results: dict
    created_at: str


class SqliteBacktester:
    def __init__(self, database_path: Path, artifact_root: Path) -> None:
        self._prices = SqlitePriceDatasetRepository(database_path, artifact_root)
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )

    def run(
        self,
        dataset_id: str,
        *,
        ticker: str,
        benchmark: str,
        short_window: int,
        long_window: int,
        initial_cash: Decimal,
        transaction_cost_bps: Decimal,
    ) -> BacktestArtifact:
        ticker = _ticker(ticker, "ticker")
        benchmark = _ticker(benchmark, "benchmark")
        if short_window < 1 or long_window <= short_window:
            raise BacktestError("Windows require 1 <= short_window < long_window")
        if not initial_cash.is_finite() or initial_cash <= 0:
            raise BacktestError("Initial cash must be positive")
        if not transaction_cost_bps.is_finite() or transaction_cost_bps < 0:
            raise BacktestError("Transaction cost must be nonnegative")

        dataset = self._prices.get(dataset_id)
        observations = self._prices.observations(dataset_id)
        series = {ticker: {}, benchmark: {}}
        for item in observations:
            if item.ticker in series:
                series[item.ticker][item.date] = item.adjusted_close
        missing = [symbol for symbol, values in series.items() if not values]
        if missing:
            raise BacktestError(
                f"Dataset has no observations for: {', '.join(missing)}"
            )
        dates = sorted(set(series[ticker]) & set(series[benchmark]))
        if len(dates) < long_window + 2:
            raise BacktestError(
                "Insufficient common observations for windows and next-day execution"
            )
        prices = [series[ticker][day] for day in dates]
        benchmark_prices = [series[benchmark][day] for day in dates]
        results = _simulate(
            dates,
            prices,
            benchmark_prices,
            short_window=short_window,
            long_window=long_window,
            initial_cash=initial_cash,
            transaction_cost_bps=transaction_cost_bps,
        )
        results.update(
            {
                "dataset_sha256": dataset.content_sha256,
                "adjustment_note": dataset.adjustment_note,
                "warning": (
                    "Historical simulation is not a forecast or trade recommendation."
                ),
            }
        )
        parameters = {
            "initial_cash": str(initial_cash),
            "long_window": long_window,
            "short_window": short_window,
            "transaction_cost_bps": str(transaction_cost_bps),
        }
        model = BacktestArtifactModel(
            backtest_id=str(uuid4()),
            dataset_id=dataset_id,
            ticker=ticker,
            benchmark=benchmark,
            strategy=STRATEGY,
            strategy_version=STRATEGY_VERSION,
            parameters_json=json.dumps(parameters, sort_keys=True),
            results_json=json.dumps(results, sort_keys=True),
            created_at=datetime.now(UTC).isoformat(),
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _from_model(model)

    def get(self, backtest_id: str) -> BacktestArtifact:
        with self._sessions() as session:
            model = session.get(BacktestArtifactModel, backtest_id)
            if model is None:
                raise BacktestError(f"Backtest not found: {backtest_id}")
            return _from_model(model)


def _simulate(
    dates: list[str],
    prices: list[Decimal],
    benchmark_prices: list[Decimal],
    *,
    short_window: int,
    long_window: int,
    initial_cash: Decimal,
    transaction_cost_bps: Decimal,
) -> dict:
    cost_rate = transaction_cost_bps / Decimal(10_000)
    cash = initial_cash
    shares = Decimal(0)
    target = 0
    pending: tuple[int, str] | None = None
    trades: list[dict] = []
    equity_curve: list[Decimal] = []
    for index, (day, price) in enumerate(zip(dates, prices, strict=True)):
        if pending is not None and pending[0] != target:
            desired, signal_date = pending
            if desired == 1:
                shares = cash / (price * (Decimal(1) + cost_rate))
                gross = shares * price
                cost = gross * cost_rate
                cash -= gross + cost
                side = "enter"
            else:
                gross = shares * price
                cost = gross * cost_rate
                cash += gross - cost
                shares = Decimal(0)
                side = "exit"
            target = desired
            trades.append(
                {
                    "cost": _number(cost),
                    "execution_date": day,
                    "price": str(price),
                    "side": side,
                    "signal_date": signal_date,
                }
            )
        pending = None
        equity_curve.append(cash + shares * price)
        if index + 1 < len(dates) and index + 1 >= long_window:
            short_average = sum(prices[index + 1 - short_window : index + 1]) / Decimal(
                short_window
            )
            long_average = sum(prices[index + 1 - long_window : index + 1]) / Decimal(
                long_window
            )
            pending = (int(short_average > long_average), day)

    returns = _returns(equity_curve)
    benchmark_curve = [
        initial_cash * value / benchmark_prices[0] for value in benchmark_prices
    ]
    return {
        "annualized_volatility": _number(statistics.stdev(returns) * math.sqrt(252)),
        "benchmark_return": _number(benchmark_curve[-1] / benchmark_curve[0] - 1),
        "common_observations": len(dates),
        "end_date": dates[-1],
        "ending_value": _number(equity_curve[-1]),
        "max_drawdown": _number(_max_drawdown(equity_curve)),
        "start_date": dates[0],
        "total_return": _number(equity_curve[-1] / initial_cash - 1),
        "total_transaction_cost": _number(
            sum(Decimal(item["cost"]) for item in trades)
        ),
        "trades": trades,
    }


def _returns(values: list[Decimal]) -> list[float]:
    return [
        float(current / previous - 1)
        for previous, current in zip(values, values[1:], strict=False)
    ]


def _max_drawdown(values: list[Decimal]) -> Decimal:
    peak = values[0]
    maximum = Decimal(0)
    for value in values:
        peak = max(peak, value)
        maximum = min(maximum, value / peak - 1)
    return maximum


def _number(value: Decimal | float) -> str:
    return format(float(value), ".10f")


def _ticker(value: str, label: str) -> str:
    normalized = value.strip().upper()
    if not _TICKER.fullmatch(normalized):
        raise BacktestError(f"Invalid {label} ticker")
    return normalized


def _from_model(model: BacktestArtifactModel) -> BacktestArtifact:
    return BacktestArtifact(
        backtest_id=model.backtest_id,
        dataset_id=model.dataset_id,
        ticker=model.ticker,
        benchmark=model.benchmark,
        strategy=model.strategy,
        strategy_version=model.strategy_version,
        parameters=json.loads(model.parameters_json),
        results=json.loads(model.results_json),
        created_at=model.created_at,
    )
