# ADR-0020: Scope Milestone 10 as automatic read-only market data

- Status: Accepted
- Date: 2026-07-02

## Context

Manual CSV export/import preserves reproducibility but breaks interactive
investigation. Browser-local state would hide the problem rather than solve it:
Redux or browser SQL cannot acquire market data and would create a second source
of truth outside the durable research ledger.

## Decision

Milestone 10 will introduce a read-only market-data provider boundary. The
backend fetches explicitly requested daily bars, normalizes them into the
existing immutable adjusted-price dataset contract, and persists the exact
normalized bytes in the existing artifact store and SQLite lineage.

Alpaca is implemented as the first optional adapter, but it is not a required v1
dependency because paid market-data access can be a practical blocker. When no
acceptable provider is configured, explicit CSV import remains the auditable
fallback rather than a separate browser-local state path.

The Alpaca adapter:

1. uses only `https://data.alpaca.markets/v2/stocks/bars`;
2. sends `ALPACA_API_KEY` and `ALPACA_SECRET_KEY` only as authentication headers;
3. requests `1Day`, ascending, `adjustment=all`, and an explicit feed;
4. follows pagination and rejects missing symbols, duplicate dates, and invalid
   values;
5. records symbols, dates, feed, adjustment, endpoint, and retrieval time;
6. never imports or initializes an Alpaca trading client; and
7. leaves explicit CSV import as the fallback when provider access is blocked.

## Acceptance criteria

- Fixture tests prove authentication headers, pagination, normalization, and
  secret-safe errors/provenance.
- Repeated identical normalized data reuses the immutable dataset hash.
- CLI and dashboard fetch data without export/import steps when an acceptable
  provider is configured.
- Existing screens, portfolio analysis, backtests, and monitoring immediately
  consume the fetched dataset.
- A live read-only smoke test succeeds when provider credentials and data
  entitlements are configured.
- No order, account, position, or broker endpoint exists in this codebase.

## Explicit exclusions

- streaming quotes, polling, schedules, or background refresh;
- accounts, positions, orders, trading clients, or execution;
- automatic security selection or portfolio action; and
- silent provider/feed substitution.
- requiring a paid market-data plan for the v1 research copilot.
