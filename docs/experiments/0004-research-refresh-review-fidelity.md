# Experiment 0004: Research-refresh review fidelity

- Status: Planned
- Baseline: Users manually compare complete memos and alert history

## Hypothesis

A deterministic review packet will reduce omitted evidence and limitation
changes while preserving period semantics and human authority.

## Metrics

- fixture truth-table accuracy for every delta category;
- false same-period revision labels;
- missing or mislinked alert records;
- duplicate review artifacts;
- reconstruction after restart;
- eligibility rejection accuracy; and
- source-artifact mutations.

## Acceptance threshold

- Every fixture delta appears in exactly one expected category.
- Cross-period values are explicitly marked as period shifts and never labeled
  revisions or restatements.
- Repeated comparison returns the same artifact.
- Linked alerts retain their IDs, evidence, and derived status.
- Different-company, reversed-time, incomplete, and missing-memo pairs fail.
- A second human outcome fails and no prior artifact changes.

## Removal path

If deterministic comparison cannot preserve fiscal-period and lineage semantics,
remove the review commands/tables while retaining the underlying immutable
research, monitoring, and human-decision records.
