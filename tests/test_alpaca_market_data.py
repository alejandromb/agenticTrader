from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest

from agentic_trading.alpaca_market_data import (
    AlpacaHistoricalDataClient,
    AlpacaMarketDataError,
    fetch_and_store_alpaca_prices,
)
from agentic_trading.market_data import SqlitePriceDatasetRepository
from agentic_trading.migrations import upgrade_database


class PaginatedTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, str]]] = []

    def __call__(self, url: str, headers: dict[str, str]) -> dict:
        self.calls.append((url, headers))
        query = parse_qs(urlparse(url).query)
        if "page_token" not in query:
            return {
                "bars": {
                    "AAPL": [
                        {"t": "2026-01-02T05:00:00Z", "c": 101.25},
                        {"t": "2026-01-03T05:00:00Z", "c": 102},
                    ]
                },
                "next_page_token": "page-2",
            }
        assert query["page_token"] == ["page-2"]
        return {
            "bars": {
                "SPY": [
                    {"t": "2026-01-02T05:00:00Z", "c": 501.5},
                    {"t": "2026-01-03T05:00:00Z", "c": 503},
                ]
            },
            "next_page_token": None,
        }


def test_fetches_paginated_adjusted_daily_bars_without_trading_api() -> None:
    transport = PaginatedTransport()
    snapshot = AlpacaHistoricalDataClient(
        "key-value", "secret-value", transport=transport
    ).fetch_daily_adjusted_closes(
        ["aapl", "SPY"], start="2026-01-02", end="2026-01-03"
    )

    assert snapshot.payload == (
        b"ticker,date,adjusted_close\n"
        b"AAPL,2026-01-02,101.25\n"
        b"AAPL,2026-01-03,102\n"
        b"SPY,2026-01-02,501.5\n"
        b"SPY,2026-01-03,503\n"
    )
    assert snapshot.row_count == 4
    assert len(transport.calls) == 2
    first_url, headers = transport.calls[0]
    query = parse_qs(urlparse(first_url).query)
    assert query == {
        "adjustment": ["all"],
        "end": ["2026-01-03"],
        "feed": ["iex"],
        "limit": ["10000"],
        "sort": ["asc"],
        "start": ["2026-01-02"],
        "symbols": ["AAPL,SPY"],
        "timeframe": ["1Day"],
    }
    assert headers["APCA-API-KEY-ID"] == "key-value"
    assert headers["APCA-API-SECRET-KEY"] == "secret-value"
    assert "key-value" not in snapshot.source
    assert "secret-value" not in snapshot.source


def test_fetched_snapshot_uses_existing_immutable_dataset_contract(
    tmp_path: Path,
) -> None:
    database = tmp_path / "state.db"
    artifacts = tmp_path / "artifacts"
    upgrade_database(database)
    transport = PaginatedTransport()

    first = fetch_and_store_alpaca_prices(
        database,
        artifacts,
        api_key="key",
        secret_key="secret",
        symbols=["AAPL", "SPY"],
        start="2026-01-02",
        end="2026-01-03",
        transport=transport,
    )
    second = fetch_and_store_alpaca_prices(
        database,
        artifacts,
        api_key="key",
        secret_key="secret",
        symbols=["AAPL", "SPY"],
        start="2026-01-02",
        end="2026-01-03",
        transport=PaginatedTransport(),
    )

    assert second.dataset_id == first.dataset_id
    observations = SqlitePriceDatasetRepository(
        database, artifacts
    ).observations(first.dataset_id)
    assert len(observations) == 4
    assert first.start_date == "2026-01-02"
    assert first.end_date == "2026-01-03"
    assert "adjustment=all" in first.source


@pytest.mark.parametrize(
    ("symbols", "start", "end", "feed", "message"),
    [
        ([], "2026-01-01", "2026-01-02", "iex", "ticker"),
        (["bad ticker"], "2026-01-01", "2026-01-02", "iex", "format"),
        (["AAPL"], "2026-01-03", "2026-01-02", "iex", "precede"),
        (["AAPL"], "2026-01-01", "2026-01-02", "unknown", "feed"),
    ],
)
def test_rejects_invalid_requests(symbols, start, end, feed, message) -> None:
    client = AlpacaHistoricalDataClient("key", "secret", transport=lambda *_: {})

    with pytest.raises(AlpacaMarketDataError, match=message):
        client.fetch_daily_adjusted_closes(
            symbols, start=start, end=end, feed=feed
        )


def test_rejects_missing_symbol_data() -> None:
    client = AlpacaHistoricalDataClient(
        "key",
        "secret",
        transport=lambda *_: {
            "bars": {"AAPL": [{"t": "2026-01-02T05:00:00Z", "c": 100}]},
            "next_page_token": None,
        },
    )

    with pytest.raises(AlpacaMarketDataError, match="SPY"):
        client.fetch_daily_adjusted_closes(
            ["AAPL", "SPY"], start="2026-01-01", end="2026-01-02"
        )
