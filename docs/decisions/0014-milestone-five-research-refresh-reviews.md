# ADR-0014: Scope Milestone 5 as research-refresh reviews

- Status: Accepted
- Date: 2026-07-01

## Context

The platform can preserve a research decision and monitor explicit price-based
criteria, but it cannot answer the next operational question: what changed when
newer research for the same company becomes available? Reading two complete
memos manually risks overlooking new evidence, resolved limitations, period
changes, or alerts that occurred between reviews.

An automated comparison can also mislead if it compares different companies,
silently treats different fiscal periods as revisions, asks a model to decide
whether a thesis is better, or changes the human disposition automatically.

## Decision

Milestone 5 will add immutable, deterministic research-refresh reviews:

1. compare two completed research runs with persisted canonical memos;
2. require matching ticker and a strictly later current `as_of` boundary;
3. compare exact-period claim inventories without calling a new value a
   restatement;
4. compare the latest supported numeric metric per concept while preserving both
   period labels and explicitly flagging period shifts;
5. identify added and resolved known limitations using normalized text;
6. record changed memo-section hashes and both section summaries without
   assigning positive or negative meaning;
7. link durable monitor alerts associated with the baseline run; and
8. collect a separate append-only human review outcome.

The comparison is idempotent by baseline/current run pair. Every output retains
the exact run, memo, claim, and alert identities used. Supported human outcomes
are `no_thesis_change`, `revise_thesis`, `investigate`, and `close_watch`.
Recording an outcome does not mutate either memo, disposition, monitor, alert,
holding, or external system.

SQLite and SQLAlchemy remain appropriate because reviews are relational joins
over bounded structured artifacts. NoSQL is not introduced without a measured
storage or query constraint.

## Explicit exclusions

- automatic SEC refreshes or scheduled research;
- LLM-written change interpretation or materiality judgment;
- labeling cross-period differences as revisions or restatements;
- automatic monitor closure, disposition changes, portfolio actions, or orders;
- news, sentiment, alternative data, broker, or DiveTrader integration; and
- deletion or mutation of historical research and review artifacts.

## Acceptance criteria

Milestone 5 is accepted when documented CLI workflows can compare two eligible
same-company runs, reconstruct an idempotent review after restart, expose exact-
period evidence deltas, period-labeled numeric deltas, limitation changes,
section changes, and linked alerts, then record one human outcome. Tests must
reject reversed time, different tickers, incomplete runs, missing memos, and a
second outcome while proving no source artifact is mutated.

## Consequences

- Research refresh becomes an auditable comparison rather than a memory task.
- Period shifts and same-period revisions remain semantically distinct.
- Whether a change matters remains a human judgment until a separate measured
  experiment justifies additional interpretation.
