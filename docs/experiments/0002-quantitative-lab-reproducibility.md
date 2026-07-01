# Experiment 0002: Quantitative lab reproducibility

- Status: Planned
- Baseline: Version 2 has no portfolio, screening, or backtest workflow

## Hypothesis

Deterministic point-in-time quantitative artifacts will improve comparability
and risk visibility without weakening evidence lineage or creating execution
authority.

## Metrics

- identical-input result reproducibility;
- rejected invalid-data cases;
- look-ahead violations detected;
- transaction costs included;
- artifact reconstruction after restart;
- runtime and storage size; and
- number of manual assumptions required.

## Acceptance threshold

- Repeated runs over the same dataset hash are identical.
- Every malformed-data and temporal-integrity fixture fails explicitly.
- Backtest signals execute on the next observation and include nonzero costs.
- Portfolio and benchmark statistics use aligned dates.
- No command writes holdings, creates orders, or accesses a broker.
