# Experiment 0002: Quantitative lab reproducibility

- Status: Accepted
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

## Result

- Exact repeated inputs produced identical parameter and result payloads.
- Invalid price, holdings, window, and observation-count fixtures failed
  explicitly.
- Every simulated trade records a signal date strictly before its execution
  date, and the cost-bearing fixture recorded nonzero transaction costs.
- Portfolio and benchmark calculations use the intersection of their dates.
- Persisted price, screen, portfolio, and backtest artifacts are reconstructable
  after a new repository/service instance is created.
- Static inspection and CLI acceptance tests confirm the quantitative commands
  contain no broker client, order model, or holdings mutation path.
