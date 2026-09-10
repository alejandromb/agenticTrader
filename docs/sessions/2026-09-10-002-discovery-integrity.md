# Session: Broader discovery and integrity

Objective: begin the approved research upgrade using existing brokerage tools.

Created separate liquid-stock scanner with verified filter enums: stocks,
market cap >= $2B, 30 daily bars of average volume >= 500,000 shares (all-session
provider expression). Existing Untitled Scan untouched. New scan returned 399
matches but only 200 rows sorted Last descending. Retained raw response privately;
these are not investment rankings. Original scanner had zero matches.

Read 14-day high-market-cap earnings calendar. Normalizer retained 50 event
records, collapsed one exact duplicate, quarantined two old fiscal-year records.
These counts refer to events, not distinct companies or verified investments.
Archived raw input and output via content-addressed store. CLI replay is local,
read-only with respect to brokerage. No live connector embedded in Python app.

Tests: 15 new cases for duplicates, conflicting records, malformed/old events,
window bounds, zero EPS, empty data and content-addressed replay. Full suite
205 tests passed; Ruff and whitespace checks pass.

Next: address capped scanner retrieval before market-wide ranking; add persistent
candidate transitions and completed normalized cash-flow valuations. Work-package
acceptance gates and prospective paper evaluation requirements are documented.
No research edge established, trade placed, bot scheduled, or key changed.
