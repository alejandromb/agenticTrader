# Experiment 0009: Read-only market-data provider boundary

- Status: Planned
- Baseline: Manual adjusted-price CSV import

## Observed limitation

An operator must leave the investigation, obtain or export a CSV, verify its
shape, and import it before using portfolio, backtest, or monitoring workflows.

## Hypothesis

A read-only historical-data provider boundary can reduce the normal workflow to
one form submission when provider access is available, while preserving the
existing immutable dataset contract. Paid market-data access must not become a
v1 requirement.

## Metrics

- operator file export/import steps;
- normalized row and date fidelity;
- provider pagination/completeness;
- immutable hash reuse;
- missing-symbol and malformed-response detection;
- credential leakage in output, errors, or persisted provenance;
- compatibility with existing quantitative workflows; and
- number of account/trading/order capabilities introduced.

## Acceptance threshold

- Normal workflow requires zero local files when a configured low-friction
  provider is available.
- Fixture output matches expected ticker/date/adjusted-close rows exactly.
- Repeated identical data returns the same dataset.
- All existing quantitative regression tests remain green.
- Credentials never appear in API output, logs, errors, or persistence.
- Exactly zero trading/account/order capabilities are introduced.
- If paid provider access is blocked, explicit CSV import remains the auditable
  fallback rather than browser-local shadow state.
