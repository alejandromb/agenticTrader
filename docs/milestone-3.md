# Milestone 3 Product Contract

## Outcome

Add reproducible quantitative research without expanding into trading or
autonomous allocation.

## Required workflows

```text
import-prices DATASET.csv --source SOURCE
screen-research --as-of TIMESTAMP [metric filters]
analyze-portfolio HOLDINGS.csv --dataset DATASET_ID --benchmark TICKER
backtest DATASET_ID --strategy STRATEGY --benchmark TICKER
```

## Price dataset contract

Required CSV columns:

| Column | Rule |
| --- | --- |
| `ticker` | Uppercase U.S. equity identifier |
| `date` | ISO date |
| `adjusted_close` | Positive decimal |

Rows must be unique by ticker/date. Dates for each ticker must be strictly
increasing after canonical sorting. Missing dates are retained as missing; they
are never forward-filled silently. The importer stores the exact source bytes
and SHA-256 hash.

## Holdings contract

Required CSV columns are `ticker` and positive `shares`. Holdings are
hypothetical and read-only. Portfolio analysis uses the latest common date not
after the requested `as_of` boundary.

## Quantitative safeguards

- Signals at date `t` execute no earlier than the next available observation.
- Transaction costs are deducted on each turnover event.
- Benchmark dates and portfolio dates use an explicit intersection.
- Adjusted-price assumptions are disclosed.
- No annualized metric is calculated from an insufficient sample.
- Backtest parameters and strategy version are persisted.
- Results include the warning that historical simulation is not a forecast.

## Non-goals

No live feeds, optimization, order generation, position sizing advice, broker
integration, or automatic portfolio mutation.
