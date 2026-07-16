"""Read-only Alpaca historical bars normalized into immutable price datasets."""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from agentic_trading.market_data import PriceDataset, SqlitePriceDatasetRepository

ALPACA_BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"
_TICKER = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")
_FEEDS = {"iex", "sip"}
_MAX_PAGES = 100


class AlpacaMarketDataError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AlpacaPriceSnapshot:
    payload: bytes
    source: str
    adjustment_note: str
    symbols: tuple[str, ...]
    start: str
    end: str
    feed: str
    row_count: int


Transport = Callable[[str, dict[str, str]], dict[str, Any]]


class AlpacaHistoricalDataClient:
    """Access only Alpaca's historical stock-bars endpoint."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        transport: Transport | None = None,
    ) -> None:
        if not api_key.strip() or not secret_key.strip():
            raise AlpacaMarketDataError("Alpaca market-data credentials are required")
        self._headers = {
            "APCA-API-KEY-ID": api_key.strip(),
            "APCA-API-SECRET-KEY": secret_key.strip(),
            "Accept": "application/json",
        }
        self._transport = transport or _request_json

    def fetch_daily_adjusted_closes(
        self,
        symbols: Sequence[str],
        *,
        start: str,
        end: str,
        feed: str = "iex",
    ) -> AlpacaPriceSnapshot:
        normalized_symbols = _validate_request(symbols, start, end, feed)
        rows: dict[tuple[str, str], Decimal] = {}
        page_token: str | None = None
        seen_tokens: set[str] = set()
        for _ in range(_MAX_PAGES):
            query = {
                "symbols": ",".join(normalized_symbols),
                "timeframe": "1Day",
                "start": start,
                "end": end,
                "limit": "10000",
                "adjustment": "all",
                "feed": feed,
                "sort": "asc",
            }
            if page_token is not None:
                query["page_token"] = page_token
            response = self._transport(
                f"{ALPACA_BARS_URL}?{urlencode(query)}", dict(self._headers)
            )
            _collect_rows(response, normalized_symbols, rows)
            value = response.get("next_page_token")
            if value in {None, ""}:
                break
            if not isinstance(value, str) or value in seen_tokens:
                raise AlpacaMarketDataError("Alpaca pagination token is invalid")
            seen_tokens.add(value)
            page_token = value
        else:
            raise AlpacaMarketDataError("Alpaca pagination exceeded the safety limit")
        present = {ticker for ticker, _ in rows}
        missing = sorted(set(normalized_symbols) - present)
        if missing:
            raise AlpacaMarketDataError(
                "Alpaca returned no daily bars for: " + ", ".join(missing)
            )
        payload = _canonical_csv(rows)
        source = (
            f"Alpaca Market Data v2 historical stock bars; endpoint={ALPACA_BARS_URL}; "
            f"symbols={','.join(normalized_symbols)}; start={start}; end={end}; "
            f"timeframe=1Day; feed={feed}; adjustment=all; sort=asc"
        )
        return AlpacaPriceSnapshot(
            payload=payload,
            source=source,
            adjustment_note=(
                "Alpaca historical daily closing prices requested with "
                "adjustment=all. Feed coverage is recorded in source metadata."
            ),
            symbols=normalized_symbols,
            start=start,
            end=end,
            feed=feed,
            row_count=len(rows),
        )


def fetch_and_store_alpaca_prices(
    database_path: Path,
    artifact_root: Path,
    *,
    api_key: str,
    secret_key: str,
    symbols: Sequence[str],
    start: str,
    end: str,
    feed: str = "iex",
    transport: Transport | None = None,
) -> PriceDataset:
    snapshot = AlpacaHistoricalDataClient(
        api_key, secret_key, transport=transport
    ).fetch_daily_adjusted_closes(symbols, start=start, end=end, feed=feed)
    return SqlitePriceDatasetRepository(database_path, artifact_root).import_bytes(
        snapshot.payload,
        source=snapshot.source,
        adjustment_note=snapshot.adjustment_note,
    )


def _validate_request(
    symbols: Sequence[str], start: str, end: str, feed: str
) -> tuple[str, ...]:
    normalized = tuple(
        dict.fromkeys(symbol.strip().upper() for symbol in symbols if symbol.strip())
    )
    if not normalized:
        raise AlpacaMarketDataError("At least one ticker is required")
    if len(normalized) > 50:
        raise AlpacaMarketDataError("At most 50 tickers may be requested")
    if any(not _TICKER.fullmatch(symbol) for symbol in normalized):
        raise AlpacaMarketDataError("Ticker format is invalid")
    try:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
    except ValueError as error:
        raise AlpacaMarketDataError("Start and end must use YYYY-MM-DD") from error
    if end_date < start_date:
        raise AlpacaMarketDataError("End date must not precede start date")
    if feed not in _FEEDS:
        raise AlpacaMarketDataError("Alpaca feed must be iex or sip")
    return normalized


def _collect_rows(
    response: dict[str, Any],
    symbols: tuple[str, ...],
    rows: dict[tuple[str, str], Decimal],
) -> None:
    bars = response.get("bars")
    if not isinstance(bars, dict):
        raise AlpacaMarketDataError("Alpaca response is missing the bars object")
    for symbol, values in bars.items():
        if symbol not in symbols or not isinstance(values, list):
            raise AlpacaMarketDataError("Alpaca response contains invalid bar data")
        for bar in values:
            if not isinstance(bar, dict):
                raise AlpacaMarketDataError("Alpaca response contains an invalid bar")
            timestamp = bar.get("t")
            if not isinstance(timestamp, str):
                raise AlpacaMarketDataError("Alpaca bar timestamp is missing")
            try:
                day = date.fromisoformat(timestamp[:10]).isoformat()
                close = Decimal(str(bar["c"]))
            except (KeyError, ValueError, InvalidOperation) as error:
                raise AlpacaMarketDataError("Alpaca bar value is invalid") from error
            if not close.is_finite() or close <= 0:
                raise AlpacaMarketDataError("Alpaca closing price must be positive")
            key = (symbol, day)
            if key in rows:
                raise AlpacaMarketDataError(
                    f"Alpaca returned a duplicate daily bar for {symbol} {day}"
                )
            rows[key] = close


def _canonical_csv(rows: dict[tuple[str, str], Decimal]) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(("ticker", "date", "adjusted_close"))
    for (ticker, day), close in sorted(rows.items()):
        writer.writerow((ticker, day, str(close)))
    return output.getvalue().encode()


def _request_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:  # noqa: S310
            value = json.load(response)
    except HTTPError as error:
        message = "Alpaca market-data request failed"
        try:
            payload = json.loads(error.read())
            if isinstance(payload, dict) and isinstance(payload.get("message"), str):
                message = f"{message}: {payload['message']}"
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        raise AlpacaMarketDataError(message) from error
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise AlpacaMarketDataError("Alpaca market-data request failed") from error
    if not isinstance(value, dict):
        raise AlpacaMarketDataError("Alpaca response must be a JSON object")
    return value
