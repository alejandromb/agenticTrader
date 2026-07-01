# Milestone 5 Acceptance Audit

- Date: 2026-07-01
- Result: Accepted
- Scope: Deterministic research-refresh reviews
- Database schema: `20260701_0017`

## Product-contract audit

| Requirement | Authoritative evidence | Result |
| --- | --- | --- |
| Eligible pair | Tests reject incomplete runs, missing memos, different tickers, identical/reversed boundaries | Pass |
| Immutable identity | Database uniqueness and restart test return one baseline/current review | Pass |
| Exact-period claims | Full type/taxonomy/concept/unit/start/end identity covers all four delta categories | Pass |
| Period semantics | Latest revenue comparison retains both periods and explicitly sets `period_shift` | Pass |
| No false revision label | Cross-period fixture output contains no revision/restatement classification | Pass |
| Metric lineage | Values, periods, units, claim IDs, absolute change, and zero-safe percentage calculation persist | Pass |
| Limitation changes | Added, resolved, and normalized unchanged fixture results match expected values | Pass |
| Section changes | Only changed summaries persist with baseline/current SHA-256 hashes | Pass |
| Alert linkage | Baseline monitor alerts are bounded between run dates and retain evidence plus derived status | Pass |
| Human authority | One append-only outcome with required rationale; no automatic action follows | Pass |
| Source immutability | Memo JSON, source hashes, and alert evidence match before and after outcome | Pass |
| CLI lifecycle | Compare, repeat, record outcome, and show persisted review are integration-tested | Pass |
| No autonomous action | Review module has no model, scheduler, notification, portfolio, broker, or order dependency | Pass |

## Known limitations

- The workflow compares already completed research; it does not fetch or schedule
  a new filing analysis.
- Exact claim identity depends on stable taxonomy/concept extraction. An alias or
  extraction-method change may appear as one removal plus one addition.
- Latest metrics are selected by reported ISO period, not by economic
  materiality. Comparisons can be valid but decision-irrelevant.
- Section comparison detects text changes, not semantic equivalence or whether
  the thesis became stronger or weaker.
- Limitation normalization handles case, trailing whitespace, and terminal
  periods; it is not semantic deduplication.
- Alert linkage includes only monitors attached to the baseline run and
  evaluations inside the review window.
- The human outcome is a review record. `close_watch` does not close or mutate a
  monitor; such lifecycle behavior requires a separate explicit design.

## Verification

- Automated suite: 106 tests passed before documentation finalization.
- Migration reached `20260701_0017` with unique review-pair and outcome
  constraints.
- Targeted fixtures cover every delta category, temporal alert exclusion,
  restart reconstruction, acknowledgement status, and source immutability.
- Formatting, lint, whitespace, and prohibited-integration scope checks passed.
