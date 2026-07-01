from pathlib import Path

import pytest

from agentic_trading.market_data import SqlitePriceDatasetRepository
from agentic_trading.migrations import upgrade_database
from agentic_trading.portfolio_analytics import (
    PortfolioAnalysisError,
    SqlitePortfolioAnalyzer,
)

FIXTURES = Path(__file__).parent / "fixtures"


def setup_analyzer(tmp_path):
    database = tmp_path / "state.db"
    artifacts = tmp_path / "artifacts"
    upgrade_database(database)
    dataset = SqlitePriceDatasetRepository(database, artifacts).import_csv(
        FIXTURES / "prices-valid.csv", source="Test fixture"
    )
    return SqlitePortfolioAnalyzer(database, artifacts), dataset


def test_analysis_is_point_in_time_persisted_and_retrievable(tmp_path) -> None:
    analyzer, dataset = setup_analyzer(tmp_path)

    artifact = analyzer.analyze(
        FIXTURES / "holdings-valid.csv",
        dataset_id=dataset.dataset_id,
        benchmark="spy",
        as_of="2025-01-06",
    )

    assert artifact.valuation_date == "2025-01-06"
    assert artifact.benchmark == "SPY"
    assert artifact.results["common_observations"] == 3
    assert artifact.results["total_value"] == "199.50"
    assert artifact.results["positions"] == [
        {
            "ticker": "AAPL",
            "shares": "2",
            "adjusted_close": "99.75",
            "market_value": "199.50",
            "weight": "1.000000",
        }
    ]
    assert artifact.results["max_weight"] == "1.000000"
    assert "not forecasts" in artifact.results["warning"]
    assert (
        Path(artifact.holdings_storage_path).read_bytes()
        == (FIXTURES / "holdings-valid.csv").read_bytes()
    )
    assert analyzer.get(artifact.analysis_id) == artifact


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ("ticker,shares\nAAPL,1\nAAPL,2\n", "Duplicate holding"),
        ("ticker,shares\nAAPL,0\n", "Shares must be positive"),
        ("ticker,weight\nAAPL,1\n", "requires ticker,shares"),
    ],
)
def test_invalid_holdings_fail_explicitly(tmp_path, payload: str, message: str) -> None:
    analyzer, dataset = setup_analyzer(tmp_path)
    holdings = tmp_path / "holdings.csv"
    holdings.write_text(payload)

    with pytest.raises(PortfolioAnalysisError, match=message):
        analyzer.analyze(
            holdings,
            dataset_id=dataset.dataset_id,
            benchmark="SPY",
            as_of="2025-01-06",
        )


def test_missing_price_history_fails_explicitly(tmp_path) -> None:
    analyzer, dataset = setup_analyzer(tmp_path)
    holdings = tmp_path / "holdings.csv"
    holdings.write_text("ticker,shares\nMSFT,1\n")

    with pytest.raises(PortfolioAnalysisError, match="MSFT"):
        analyzer.analyze(
            holdings,
            dataset_id=dataset.dataset_id,
            benchmark="SPY",
            as_of="2025-01-06",
        )
