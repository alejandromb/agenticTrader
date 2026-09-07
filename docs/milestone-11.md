# Milestone 11: Portfolio context alongside research

- Status: In progress; snapshot storage foundation implemented
- Date: 2026-09-07

## Outcome

Open the dashboard, understand account exposure, select a holding, and review
its saved research and limitations without exporting or importing files.
Measure reduced navigation and preserved evidence, not investment returns.

## Workflow

1. Select an explicitly identified account and request a refresh.
2. Retrieve read-only portfolio totals, all pages of equity positions, and
   corresponding quotes through an authorized connection.
3. Save an immutable local snapshot with source and collection timestamps.
4. Display account value, cash, buying power, holdings, and concentration with
   coverage and freshness visible. Preserve the prior snapshot on refresh failure.
5. Select a holding to open its saved research; preserve the selected account,
   snapshot, and ticker when navigating between views and after a reload.
6. Review or record a human research disposition through the existing workflow.

## Snapshot contract

- Use the existing SQLAlchemy/Alembic stack and local artifact storage.
- Retain schema version, snapshot ID, opaque local account reference, provider,
  collection start/end, source timestamps when supplied, currency, content hash,
  coverage status, and explicit limitations. Missing source time is unknown;
  retrieval time is not a substitute for a market timestamp.
- Store account value, cash, pending deposits, buying power, and unleveraged
  buying power as distinct broker-reported fields. Do not infer margin debt,
  maintenance requirements, or a margin call from their differences.
- Retain equity symbol, signed quantity, optional average cost, quote and quote
  timestamp. Use decimal arithmetic. Unknown cost/price remains null, never zero.
- Retain other asset-class totals as coverage context. Equity-only detail must
  not be labeled a complete holdings inventory when other assets are present.
- Treat pagination failure, missing quotes, duplicate/conflicting positions,
  unsupported currencies, and source errors explicitly. A failed collection
  must not replace the latest complete snapshot with an apparently empty account.
- Keep snapshots immutable; separate refresh-attempt records from content.
  Identical content can reuse a hash while each retrieval retains its own time.
- Broker account identifiers remain private runtime mappings. Tokens must never
  enter snapshots, logs, browser state, test fixtures, or Git. Store sensitive
  runtime artifacts only in ignored local data directories; Git ignore is not
  encryption or a backup. Tests use synthetic accounts and holdings only.

## Calculations and evidence

Position value = signed quantity × observed quote. Estimated unrealized result
= quantity × (quote − average cost), labeled as an estimate, not tax-lot P&L.
Initially support these calculations for long equity positions; mark short or
boxed positions unsupported for derived portfolio concentration until defined.

Show equity weight = position value / sum of priced long-equity values only
when equity coverage is complete and the denominator is positive. Otherwise
show unavailable with the reason. If showing account weight, separately label
position value / broker account value; do not imply these weights sum to 100%.
Broker totals and quote-derived totals are distinct observations and may differ.
Mixed currencies are not summed without an explicit conversion source.

Link research by ticker plus resolved issuer identity where available. Preserve
the selected run/memo ID and filing date. A present-day snapshot linked to older
research is current review context, not a historical backtest. Missing research
must be visible; MU and SNDK are examples, not hard-coded special cases.

## Connection boundary

The chat currently exposes Robinhood read tools, including `get_portfolio` and
`get_equity_positions`; the latter requires pagination and provides no price.
Tool-schema inspection establishes available fields, not successful live app
access. The local application has no demonstrated authenticated transport yet.

Resolve supported app authorization or an authenticated local read-only bridge
before implementing live refresh. Never extract credentials from the chat or
browser. Synthetic fixtures can validate storage/UI independently, but do not
satisfy end-to-end acceptance. Manual export/import is not milestone completion.

All accounts may supply authorized research context. Agentic is the only account
designated for potential future confirmed orders under ADR-0021; this milestone
adds no order preview, placement, cancellation, or account mutation capability.

## Tasks and completion gates

| ID | Task | Done when | Dependency |
| --- | --- | --- | --- |
| P11-01 | Product contract and acceptance plan | Recorded and linked from project state | Complete |
| P11-02 | Prove authorized read transport | App or bridge reads a selected account, paginates, and handles disconnect without exposing secrets | Next |
| P11-03 | Snapshot schema and persistence | Migration, decimal validation, immutable history, restart and failure tests pass | P11-01 |
| P11-04 | Normalize provider observations | Synthetic missing-data/pagination tests and authorized transport integration pass | P11-02, P11-03 |
| P11-05 | Concentration and research links | Formula fixtures and account/run isolation tests pass | P11-03 |
| P11-06 | Compact dashboard overview | Selection survives navigation/reload; stale and incomplete states are visible | P11-04, P11-05 |
| P11-07 | Operator acceptance | Experiment 0010 passes with actual authorized refresh | P11-06 |
| BACKUP-01 | Private remote backup | User-selected remote configured and checkpoint verified remotely | Destination needed |

### Implementation checkpoint (2026-09-07)

P11-03 is partially implemented: validated decimal observations, opaque account
references, SQLAlchemy/Alembic snapshot index, verified content-addressed storage,
separate save timestamps, account-scoped retrieval, and latest complete equity
snapshot selection. Nine new tests cover validation, restart, duplicate content,
incomplete refresh, account isolation, and artifact corruption. Full suite: 146
passed. No dashboard or live account ingestion is wired yet.

Follow-up checkpoint: added collection start/end and typed failure records,
individual other-asset totals, canonical numeric/time normalization, and mixed
quote timestamp limitations. Added deterministic equity/account weights and
estimated unrealized results with null/coverage gates. Full suite: 155 passed.

Remaining: the collection service must wire snapshot saves and refresh records
into a consistent lifecycle, including interruption recovery. P11-05 calculations
are implemented, but saved research linking remains pending. Current completeness
refers only to equity positions and quote availability, not the whole account.

P11-02 discovery: Robinhood's official
[overview](https://robinhood.com/us/en/support/articles/agentic-trading-overview/)
documents HTTP MCP access for other compatible platforms. This supports exploring
a dedicated app client, but does not prove our app's authentication. No tokens
were extracted or live account data fetched during this checkpoint.

## Exclusions

No trading automation, new paid-data requirement, sector/factor/correlation
charts, LLM portfolio scorer, new database engine, or portfolio recommendation
engine. Existing research and human decision records remain authoritative.

Acceptance is defined in [Experiment 0010](experiments/0010-portfolio-context.md).
