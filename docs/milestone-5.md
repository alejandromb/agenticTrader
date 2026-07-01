# Milestone 5 Product Contract

## Outcome

Produce an auditable change packet when a newer completed research memo exists
for the same company, without generating a recommendation or changing state in
the research, monitoring, portfolio, or execution systems.

## Required workflows

```text
compare-research BASELINE_RUN_ID CURRENT_RUN_ID
show-research-review REVIEW_ID
record-review-outcome REVIEW_ID OUTCOME --rationale TEXT
```

## Eligibility

- Both runs exist and are `complete`.
- Both have canonical investment memos.
- Memo tickers match exactly.
- Current `as_of` is strictly later than baseline `as_of`.
- A baseline/current pair identifies one immutable review.

## Review packet

The persisted packet contains:

- baseline/current run and memo IDs, ticker, and `as_of` values;
- exact-period claims added, removed, changed, or unchanged;
- latest numeric metric comparisons with concept, unit, values, periods, claim
  IDs, and an explicit `period_shift` flag;
- normalized known limitations added and resolved;
- each changed memo section’s baseline/current summary and SHA-256 hashes; and
- alerts from monitors attached to the baseline run, including acknowledgement
  status and evidence.

Exact-period claim comparison uses claim type, concept, unit, period start, and
period end as the identity. Different periods are additions/removals, never
silent revisions. Latest metric comparisons are descriptive and do not infer
causality or materiality.

## Human outcome

One append-only outcome may be recorded per review:

- `no_thesis_change`
- `revise_thesis`
- `investigate`
- `close_watch`

The rationale is required. The event records a human actor and timestamp but
does not mutate a memo, disposition, monitor, alert, portfolio, or broker.

## Non-goals

No automatic research refresh, scheduled comparison, LLM interpretation,
materiality classification, notification delivery, broker access, order, or
portfolio mutation.
