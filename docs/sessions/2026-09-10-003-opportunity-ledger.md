# Session: Durable candidate reasoning

Added SQLAlchemy opportunity event model, Alembic migration 0021 and repository
with strict input validation, legal research transitions, idempotent event IDs,
monotonic decision time, fixed symbol identity, optimistic sequence checks and
database uniqueness for concurrent writes. No trade approval states. CLI offers
latest records, history and append. Existing pilot imported into private DB with
discovered origins and researching/deferred follow-up decisions, not backdated.

Read our existing scanner configuration, then tried market-cap ascending and
descending retrieval. Filters preserved; final saved sort is descending. Match
totals changed from 399 to 396; 400 distinct IDs across calls. Raw timed snapshots
retained. Coverage remains provisional, not falsely marked complete.

Validation: 13 new ledger tests plus migration schema/version assertion updated.
Initial full run caught the outdated schema-version expectation. Fixed and
reran full suite: 218 tests passed; Ruff and diff checks passed. Ledger evidence references remain unresolved
pointers; service does not certify their content. No UI ledger integration yet.

Next: expose persisted history in briefing without manual copy/export and link
candidate work to full research runs/valuation artifacts. No orders or scheduler.
