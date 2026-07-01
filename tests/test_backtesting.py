from decimal import Decimal
from pathlib import Path

import pytest

from agentic_trading.backtesting import BacktestError, SqliteBacktester
from agentic_trading.market_data import SqlitePriceDatasetRepository
from agentic_trading.migrations import upgrade_database

FIXTURE = Path(__file__).parent / "fixtures/prices-backtest.csv"


def setup_backtester(tmp_path):
    database = tmp_path / "state.db"
    artifacts = tmp_path / "artifacts"
    upgrade_database(database)
    dataset = SqlitePriceDatasetRepository(database, artifacts).import_csv(
        FIXTURE, source="Backtest fixture"
    )
    return SqliteBacktester(database, artifacts), dataset


def test_backtest_executes_signal_on_next_observation_and_deducts_costs(tmp_path):
    backtester, dataset = setup_backtester(tmp_path)

    artifact = backtester.run(
        dataset.dataset_id,
        ticker="aapl",
        benchmark="spy",
        short_window=2,
        long_window=3,
        initial_cash=Decimal("10000"),
        transaction_cost_bps=Decimal("10"),
    )

    assert artifact.strategy == "moving-average"
    assert artifact.strategy_version == "1.0"
    assert artifact.results["common_observations"] == 10
    assert artifact.results["trades"]
    assert all(
        trade["execution_date"] > trade["signal_date"]
        for trade in artifact.results["trades"]
    )
    assert Decimal(artifact.results["total_transaction_cost"]) > 0
    assert "not a forecast" in artifact.results["warning"]
    assert backtester.get(artifact.backtest_id) == artifact


def test_same_inputs_produce_same_parameters_and_results(tmp_path):
    backtester, dataset = setup_backtester(tmp_path)
    arguments = {
        "ticker": "AAPL",
        "benchmark": "SPY",
        "short_window": 2,
        "long_window": 3,
        "initial_cash": Decimal("10000"),
        "transaction_cost_bps": Decimal("10"),
    }

    first = backtester.run(dataset.dataset_id, **arguments)
    second = backtester.run(dataset.dataset_id, **arguments)

    assert second.parameters == first.parameters
    assert second.results == first.results


def test_invalid_windows_fail_explicitly(tmp_path):
    backtester, dataset = setup_backtester(tmp_path)

    with pytest.raises(BacktestError, match="short_window < long_window"):
        backtester.run(
            dataset.dataset_id,
            ticker="AAPL",
            benchmark="SPY",
            short_window=3,
            long_window=3,
            initial_cash=Decimal("10000"),
            transaction_cost_bps=Decimal("10"),
        )
