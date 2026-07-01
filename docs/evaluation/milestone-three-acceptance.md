# Milestone 3 Acceptance Audit

- Date: 2026-07-01
- Result: Accepted
- Scope: Local point-in-time quantitative lab
- Database schema: `20260701_0015`
- Strategy: `moving-average` version `1.0`

## Product-contract audit

| Requirement | Evidence | Result |
| --- | --- | --- |
| Immutable price input | Exact CSV bytes, source metadata, and SHA-256 persisted; repeated hash is idempotent | Pass |
| Temporal integrity | Duplicate/nonmonotonic data rejected; `as_of` boundaries and common-date intersections explicit | Pass |
| Deterministic screen | Memo-backed filters select the latest eligible run per ticker and exclude missing metrics | Pass |
| Portfolio analytics | Read-only shares valued with aligned benchmark dates; concentration, volatility, tracking error, and drawdown persisted | Pass |
| Look-ahead control | Signal at date `t` executes only at the next common observation | Pass |
| Cost awareness | Basis-point costs deducted and reported for every turnover event | Pass |
| Reproducibility | Identical dataset and parameters produce identical result payloads | Pass |
| Reconstruction | Dataset, portfolio, screen, and backtest artifacts persist in the ORM schema | Pass |
| Human authority | Outputs state that history is not a forecast or recommendation | Pass |
| No execution | No live feed, order, broker, rebalancing, or holdings-mutation path exists | Pass |

## Known limitations

- Imported adjusted-close quality and corporate-action treatment depend on the
  documented source; the platform does not independently verify adjustments.
- Daily observations are aligned by intersection without silent forward fill.
- Portfolio analytics assume constant shares and omit cash flows, taxes,
  dividends not represented in adjusted prices, and position history.
- The single reference strategy is deliberately simple. No parameter search,
  statistical significance claim, survivorship-bias correction, or benchmark
  constituent history is provided.
- Fractional shares are used inside the simulation to isolate strategy and cost
  behavior from lot-size effects.

## Verification

- Automated tests cover malformed inputs, persistence, deterministic repetition,
  CLI workflows, next-observation execution, costs, and schema migration.
- Formatting, lint, and whitespace checks pass.
- Fixture acceptance covers price import, portfolio analysis, and backtesting;
  the persisted WMT research database covers the deterministic screen workflow.
