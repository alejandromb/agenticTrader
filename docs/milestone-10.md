# Milestone 10 Product Contract

## Outcome

Make market-data-backed investigation dynamic without sacrificing immutable
inputs, as-of boundaries, or auditability.

## Primary workflow

1. Enter one or more tickers and an explicit date range.
2. Use a configured read-only market-data provider, if available.
3. Fetch daily adjusted bars through the backend.
4. Persist a canonical immutable price snapshot automatically.
5. Use the new dataset immediately in portfolio, backtest, and monitor forms.

Alpaca is the first optional adapter, but paid market-data access is not a v1
requirement. When provider access is blocked, explicit adjusted-price CSV import
remains the auditable fallback.

## Safety boundary

Credentials authenticate historical market-data requests only. Agentic Trading
contains no trading client and no account, position, or order operation.

## Reproducibility

Every snapshot retains the provider endpoint, symbols, date range, feed,
adjustment mode, content hash, normalized rows, and retrieval timestamp.
