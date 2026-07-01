# ADR-0012: Scope Milestone 3 as a point-in-time quantitative lab

- Status: Accepted
- Date: 2026-07-01

## Context

The roadmap places screeners, portfolio analytics, risk metrics, and backtesting
after the research decision record. These tools can create false confidence when
they use revised data, future information, survivorship-biased universes,
frictionless execution, or silently optimized parameters.

## Decision

Milestone 3 will implement a local quantitative-analysis laboratory with four
bounded capabilities:

1. import and validate point-in-time daily adjusted-price observations;
2. screen accepted research records using deterministic, as-of-bounded metrics;
3. value user-supplied hypothetical portfolios and calculate concentration,
   return, volatility, drawdown, and benchmark-relative risk; and
4. backtest versioned deterministic strategies using only information available
   before each simulated decision, next-observation execution, and explicit
   transaction costs.

Every dataset records its source, retrieval time, content hash, observation
range, and adjustment assumptions. Imported data is immutable. Backtest results
record the dataset hash, strategy version, parameters, rebalance events, costs,
and benchmark. Parameter searches are not part of this milestone.

Screening and backtest output is research evidence, not a trade recommendation.
Portfolio holdings are hypothetical user inputs and never trigger orders.

## Explicit exclusions

- live market-data feeds;
- broker accounts, orders, or execution;
- autonomous portfolio construction or rebalancing;
- options, leverage, short sales, or intraday simulation;
- opaque optimization or parameter mining;
- claims that backtested performance predicts future returns; and
- silently filling missing observations or changing the historical universe.

## Acceptance criteria

Milestone 3 is accepted when documented CLI workflows can import a fixture
dataset, reproduce a deterministic screen, analyze a hypothetical portfolio,
and run a cost-aware backtest; malformed, duplicate, non-monotonic, and
look-ahead-invalid inputs fail explicitly; every result can be reconstructed
from persisted inputs; and the complete suite passes without any execution
capability.

## Consequences

- Quantitative claims become reproducible artifacts rather than model prose.
- Data quality and time semantics are first-class architecture concerns.
- More sophisticated strategies require separate experiments under ADR-0010.
