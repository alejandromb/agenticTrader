# Opportunity decision ledger

SQLAlchemy/Alembic-backed append-only service in `opportunities.py`. Initialize
the existing database with `agentic-trading init-db` before use. No new database
technology, daemon or credentials required.

```sh
.venv/bin/python -m agentic_trading.opportunities
.venv/bin/python -m agentic_trading.opportunities --history CANDIDATE_UUID
.venv/bin/python -m agentic_trading.opportunities --append PRIVATE_EVENT_JSON
```

An event contains event_id, candidate_id (UUIDs), sequence (zero-based), symbol,
stage, recorded_at (timezone-aware), reason, evidence_refs and limitations.
Nonempty evidence and limitation entries are required. References are retained
as provenance pointers, not automatically resolved or verified. The initial
event must be discovered; subsequent events increment sequence by exactly one.
Replaying the identical event ID is idempotent; changed content is rejected.
The candidate/sequence unique constraint prevents concurrent overwrites.

Stages describe work, not achievements: discovered, researching, valuation,
deferred, rejected. Valuation means work has entered that phase, NOT that fair
value is established. There is deliberately no approved, buy or sell stage.
Reopening a rejected candidate requires a new researching event with reason;
prior rejection remains visible. Symbol identity cannot change within a history.
Multiple distinct theses may use separate candidate IDs for the same symbol.

History is append-only through this service, not tamper-proof against direct
database access. The briefing now reads ledger history directly on each request.
SHA-256 references are resolved only inside the configured artifact store and
checked for byte integrity. Arbitrary paths/URLs are never fetched; legacy path
and research-run references remain unresolved. Content integrity does not verify
claim truth, source authenticity, or valuation completion. Research-run resolution
and independently validated valuation gates remain follow-ups.
Keep actual candidate records in the private database, outside Git.

## Scanner coverage check

Two opposite market-cap sorts return the first 200 rows from either end. The
Sep 10 experiment observed totals changing between calls (399 and 396), with
400 distinct instrument IDs across both. This is a multi-time union, not a
complete point-in-time universe, and must not be used as a survivorship-free
backtest cohort. Both raw snapshots and timing are saved privately. Final saved
scanner sort is Market cap descending; filters unchanged. Resolve coverage with
bounded partitions and explicit completeness checks before broad ranking.
