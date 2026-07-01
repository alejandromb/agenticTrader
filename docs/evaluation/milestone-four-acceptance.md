# Milestone 4 Acceptance Audit

- Date: 2026-07-01
- Result: Accepted
- Scope: Deterministic decision monitoring
- Database schema: `20260701_0016`

## Product-contract audit

| Requirement | Evidence | Result |
| --- | --- | --- |
| Human eligibility | Creation requires a completed `watch` or `consider_for_portfolio` disposition | Pass |
| Immutable criteria | Exact rule bytes are content-addressed; normalized rules are persisted once | Pass |
| Strict validation | Stable IDs, supported types, uppercase tickers, finite thresholds, and unique rules enforced | Pass |
| Temporal integrity | Only observations on or before explicit `as_of` participate | Pass |
| Deterministic semantics | Price comparisons are strict; drawdown includes equality and uses observed peak through boundary | Pass |
| Evidence lineage | Evaluation retains dataset ID/hash, boundary, observed value/date, threshold, and outcome | Pass |
| Idempotency | Monitor/dataset/`as_of` uniquely identifies one evaluation | Pass |
| Alert deduplication | At most one alert exists per evaluation and triggered rule | Pass |
| Human acknowledgement | Separate append-only event derives acknowledged status without changing alert evidence | Pass |
| Restart reconstruction | A new service instance recovers the evaluation and alerts | Pass |
| No autonomous action | No scheduler, notification, model, broker, order, or portfolio mutation exists | Pass |

## Known limitations

- Evaluation is manual and local. There is no scheduler or live price feed.
- Only adjusted-price threshold and dataset-window drawdown rules are supported.
- Drawdown starts at the first ticker observation in the selected dataset, not
  at a position-entry date or human decision date.
- Dataset source quality and adjustment semantics remain the importer’s stated
  assumptions; they are not independently verified.
- Rules cannot currently be retired or superseded. Create a separate monitor to
  represent changed criteria while preserving the original history.
- Alerts are listed through the CLI and are not delivered externally.
- The system measures deterministic correctness and duplication, not whether a
  threshold improves investment outcomes. That requires longitudinal evidence.

## Verification

- Automated suite: 97 tests passed before documentation finalization.
- CLI integration covers creation, evaluation, repeated evaluation, alert
  listing, and acknowledgement.
- Migration reached `20260701_0016` with relational constraints for evaluation
  and alert uniqueness.
- Formatting, lint, whitespace, and prohibited-integration scope checks passed.
