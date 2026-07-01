# ADR-0013: Scope Milestone 4 as deterministic decision monitoring

- Status: Accepted
- Date: 2026-07-01

## Context

The platform now produces evidence-backed research decisions and reproducible
quantitative artifacts, but it does not preserve what a human wants monitored
after a decision. Without explicit criteria, follow-up becomes memory-driven,
alerts are difficult to audit, and changed evidence can be noticed late.

Monitoring can also become unsafe or noisy when a model invents thresholds,
fresh data is silently mixed with old decisions, repeated evaluations create
duplicate alerts, or an alert triggers portfolio activity.

## Decision

Milestone 4 will add a local, deterministic decision-monitoring ledger:

1. humans create a monitor only from a completed research run whose disposition
   is `watch` or `consider_for_portfolio`;
2. each monitor contains explicit, typed rules with human-supplied thresholds;
3. evaluations use a named immutable price dataset and an explicit `as_of` date;
4. every rule result records the observed value, threshold, source artifact,
   evaluation boundary, and pass/trigger status;
5. repeated evaluation of the same monitor, dataset, and boundary is idempotent;
6. a rule creates at most one durable alert per evaluation; and
7. alert acknowledgement is an append-only human event and causes no other
   action.

The first rule set is intentionally narrow: adjusted price above/below a
threshold and drawdown from the highest observed adjusted close within the
selected immutable dataset. Rules evaluate only observations on or before the
requested boundary. Missing ticker history fails explicitly.

SQLite and SQLAlchemy remain the canonical store. These records are structured,
relational, transactional, and modest in volume, so adding NoSQL would provide
no measured benefit. Storage may be reconsidered through a later ADR if volume,
query shape, or unstructured-data requirements demonstrate a real constraint.

## Explicit exclusions

- live data acquisition, polling, or background scheduling;
- email, push, Slack, or webhook delivery;
- model-generated rules or thresholds;
- news, sentiment, or alternative-data monitoring;
- automatic research reruns, dispositions, allocations, orders, or execution;
- mutation or deletion of historical evaluations and alerts; and
- integration with DiveTrader or Alpaca.

## Acceptance criteria

Milestone 4 is accepted when documented CLI workflows can create an eligible
monitor, evaluate all supported rules against an immutable fixture dataset,
reproduce the same evaluation without duplicate alerts, list triggered alerts,
and append a human acknowledgement. Tests must prove eligibility, temporal
boundaries, threshold semantics, drawdown calculation, idempotency, persistence,
and absence of execution behavior.

## Consequences

- Follow-up criteria become durable and inspectable instead of conversational.
- Alerts remain evidence records, not recommendations or actions.
- Scheduled automation and external delivery must prove value separately after
  deterministic monitoring quality is measured.
