# Project State

Last updated: 2026-09-10

Latest slice: on-request [opportunity radar](docs/opportunity-radar.md) now
separates portfolio coverage from candidate screening in the briefing. Four-name
private pilot retained evidence and deferrals; no complete valuation or new trade.
190 tests pass; scan coverage/escaping regressions included. This is a manual
workflow, not a background scanner or proven source of excess returns. Next:
finish the two shortlisted valuation reviews and preregister paper evaluation.

Daily home page: `/briefing` on the local dashboard. See
[daily briefing workflow](docs/daily-briefing.md). Reads private local JSON on
request; embedded-browser view opened successfully. 184 tests pass after this
UI slice. No live feed, automatic trading or recurring monitoring added.

Session status: Manual account loss-review foundation implemented; live transport and scheduled monitoring remain pending

New slice: [account risk checks](docs/account-risk-checks.md) preserves a fixed
baseline, adjusts for external funding, and refuses definitive results with
stale or incomplete inputs. Private daily notes retain fills and managed-account
comparison context. This is a manually invoked content-addressed artifact, not
an active bot, broker order, dashboard integration or scheduled alert.

Latest research-integrity slice: exact-filing coverage diagnostics now distinguish
absent SEC observations from unsupported metrics. A reviewed ISRG filing-scoped
cash-capex mapping preserves its original tag and YTD period. Fixed empty
primary-tag history suppressing alias fallback. Regression/full suite: 159 tests
pass with loopback access. This does not complete live portfolio integration or
add execution authority. See [session record](docs/sessions/2026-09-07-006-filing-coverage.md).

## Progress at a glance

| Work item | Status | Evidence / remaining work |
| --- | --- | --- |
| Research foundation through Milestone 9 | Accepted | Completion and validation records below |
| Milestone 10 provider implementation | Implemented | Commit `0644b2d`; optional Alpaca adapter and immutable dataset persistence |
| Milestone 10 operator acceptance | Pending | Experiment 0009 remains planned; live provider access is unverified |
| Robinhood account scope | Recorded | ADR-0021; Agentic only for potential confirmed orders |
| Portfolio-context integration in the app | Storage, refresh records and calculations implemented; live access/UI pending | [Milestone 11](docs/milestone-11.md); 155 tests pass |
| Remote repository backup | Unconfigured | No Git remote; needs a destination |
| Execution in the research app | Deferred | Requires separate ADR and product contract |

This file is the single current progress tracker. Each active slice must name
its outcome, evidence of completion, remaining limitations, and exact next step.
Session logs preserve history; ADRs preserve decisions; Git preserves changes.

## Current phase

Milestone 10 implementation is committed. Operator acceptance and future
read-only portfolio context remain separate follow-ups.

## Active objective

Resolve P11-02: prove a supported authorized read transport for the local app.
The snapshot contract and acceptance criteria are recorded in Milestone 11 and
Experiment 0010. Persistence can be developed with synthetic fixtures while
transport is investigated, but live acceptance requires a working connection.

## Completed

- Captured the project vision in `Agentic_Trading_Project_Summary.md`.
- Established that AI is advisory and humans retain investment and execution
  authority in ADR-0001.
- Established persistent project state and session logging in ADR-0002.
- Scoped version one as a U.S. equities research copilot in ADR-0003.
- Defined structured investment memos and claim-level evidence in ADR-0004.
- Added an Apple memo fixture and refined calculation and source metadata.
- Adopted a primary-source-first evidence policy in ADR-0005.
- Adopted a deterministic, resumable research workflow in ADR-0006.
- Selected Python 3.12 and a local-first stack in ADR-0007.
- Implemented memo schema and semantic validation with tests.
- Implemented the first SEC submissions and filing-discovery client with tests.
- Implemented durable SQLite runs and append-only workflow transitions.
- Replaced direct SQLite access with SQLAlchemy 2 ORM models and added the
  initial Alembic migration.
- Added a non-root Docker runtime, development/test image, and Compose-managed
  persistent volumes.
- Added a CLI for memo validation, SEC discovery, and workflow state operations.
- Added content-addressed local artifact storage with integrity verification.
- Verified live Apple filing discovery against SEC submissions data.
- Verified live Apple 10-K download, content hashing, and ORM provenance
  persistence using an identified SEC request.
- Added deterministic, period-specific SEC XBRL fact selection and verified
  fiscal 2025 Apple revenue against live company-facts data.
- Added evidence-linked candidate-claim persistence with database-enforced
  source/run consistency.
- Added and live-verified a minimum annual financial snapshot covering revenue,
  net income, assets, liabilities, and operating cash flow.
- Selected OpenAI Responses with strict Structured Outputs in ADR-0008.
- Implemented a pinned, configurable OpenAI financial-analysis adapter with
  domain-level claim-lineage validation.
- Added versioned analysis-artifact persistence with database-enforced input
  claim lineage.
- Added the Financial Analysis Evaluation Rubric v1.
- Verified the replacement API key is correctly configured and Git-ignored.
- Persisted and evaluated the first live Apple financial analysis: all gates
  passed and the artifact scored 11/12.
- Updated the financial-analysis prompt to version 1.1 from observed
  evidence-fidelity issues.
- Added a user-facing `research-company` orchestrator, secret-safe `doctor`
  command, README, and user guide.
- Live-validated `research-company WMT`; prompt v1.1 passed all gates and scored
  12/12.
- Changed missing issuer-specific XBRL concepts into explicit evidence gaps.
- Added first-class persistence for evidence gaps in analysis artifacts.
- Expanded the deterministic snapshot from five to twelve possible metrics;
  Walmart supplied eleven and one explicit evidence gap.
- Evaluated the expanded Walmart analysis at 11/12 and updated prompt v1.2 with
  accounting-containment and limited-solvency rules.
- Expanded the annual snapshot with acquisitions, shareholder distributions,
  debt activity, investing and financing cash flows, and net cash movement.
- Added a dedicated cash-allocation analysis section and prompt v1.3 rules that
  distinguish reinvestment, acquisitions, financing, and shareholder returns.
- Added source-linked narrative claims for management's stated capital-spending
  purpose, with deterministic extraction and risk-boilerplate rejection.
- Accepted ADR-0009 and added exact-accession comparative fact enumeration as
  the foundation for multi-period analysis without silent filing-context mixing.
- Added same-filing annual history extraction, period-aware trend analysis, and
  neutral cross-filing revision detection; prompt version is now 1.4.
- Live-validated Walmart prompt v1.4 with cash allocation and three-year trends;
  all gates passed and the artifact scored 12/12.
- Added a supported common-stock dividend XBRL alias discovered during the live
  evaluation.
- Added a deterministic known-limitations section that always includes every
  persisted evidence gap; prompt version is now 1.5.
- Recorded the architect's DiveTrader integration note: keep the sibling Alpaca
  prototype separate as a future execution lab, with no v1 merge or live-money
  authority and explicit safety preconditions for any later integration.
- Added a first-class cross-filing revision-audit artifact with durable ORM
  persistence and visible saved-run output.
- Added automatic revision-audit population by comparing same-period facts in
  the selected 10-K with the earliest prior 10-K observation; changed values
  retain both accessions and remain neutrally classified.
- Live-validated automatic revision auditing on Walmart: the visible audit count
  was zero because no compared annual values changed across accessions.
- Normalized known limitations to prevent duplicates that differ only by case or
  trailing punctuation.
- Added a deterministic calculation engine for revenue growth, operating and net
  margins, free-cash-flow approximation, and current ratio; every result retains
  its exact formula and filing-fact inputs.
- Persisted calculated claims with database-enforced formula and input-claim
  lineage and integrated them into research analysis; prompt version is now 1.6.
- Added deterministic capital-allocation table extraction anchored to the total
  capex row, preserving table units and period headers while rejecting unrelated
  keyword matches; verified against the captured Walmart filing.
- Live-validated prompt v1.6 with deterministic calculations and quantified
  Walmart capital allocation; acceptance review found revision-audit status was
  not included in model context.
- Added deterministic revision-audit context to structured analysis so zero
  detected revisions cannot be misreported as no comparison; prompt version is
  now 1.7.
- Live-validated prompt v1.7 and completed the README requirement audit: all
  version-one gates passed with 62 tests and durable saved-run verification.
- Accepted ADR-0011 and recorded the Version 2 product contract and experiment
  baseline.
- Added bounded Item 1 business and Item 1A risk evidence extraction with
  explicit gaps, source-linked filing-statement claims, and captured-Walmart
  verification.
- Added Version 2 structured business-quality, material-risk, bull/base/bear,
  and devil's-advocate analysis sections with claim-lineage validation; prompt
  version is now 2.0.
- Added deterministic five-year bear/base/bull cash-flow present-value scenarios
  with explicit growth, discount, terminal-growth, horizon, and base-cash-flow
  assumptions plus input-claim lineage; outputs are not equity price targets and
  prompt version is now 2.1.
- Added deterministic canonical investment-memo synthesis, schema and semantic
  validation, durable ORM persistence, saved-run visibility, and workflow
  progression to `awaiting_human_disposition`.
- Added the explicit `record-disposition` command and append-only, human-owned
  disposition event persistence; recording a valid disposition completes the
  run without mutating the memo.
- Completed the first live Version 2 Walmart workflow through a persisted memo
  and `awaiting_human_disposition`; all qualitative and valuation sections were
  populated with claim references.
- Added persisted OpenAI input/output token counts and request latency so Version
  2 quality, cost, and speed can be evaluated against the Version 1 baseline.
- Measured the final live Version 2 model call at 20,593 input tokens, 7,538
  output tokens, and 47,872 ms request latency.
- Upgraded the canonical memo contract to schema 2.0 so bull, base, bear, and
  devil's-advocate sections are independently required and preserved.
- Completed the schema-2.0 live Version 2 acceptance run and product-contract
  audit; the measured memo retained 102 claims, 86 evidence records, all required
  perspectives, valuation sensitivities, limitations, and human authority.
- Accepted ADR-0012 and recorded the Milestone 3 quantitative-lab contract and
  reproducibility experiment.
- Added immutable, content-addressed adjusted-price CSV import with source and
  adjustment metadata, strict temporal/data validation, idempotent hash reuse,
  ORM persistence, and the `import-prices` CLI command.
- Added persisted, deterministic `screen-research` over memo-backed research
  runs with strict `as_of` boundaries, latest-run-per-ticker selection, explicit
  metric filters, missing-metric exclusion, and live WMT verification.
- Added persisted hypothetical portfolio analytics over immutable adjusted-price
  datasets, including explicit as-of/benchmark date alignment, valuation,
  concentration, volatility, tracking error, and drawdown metrics.
- Added versioned, deterministic moving-average backtesting with next-observation
  execution, explicit transaction costs, aligned benchmark dates, persisted
  parameters/results, and reproducibility tests.
- Accepted the complete Milestone 3 quantitative-lab contract with documented
  known limitations and no broker, order, or portfolio-mutation path.
- Accepted ADR-0013 and recorded the Milestone 4 deterministic decision-
  monitoring contract and signal-quality experiment.
- Added immutable, content-addressed monitor rules gated by completed human
  `watch` or `consider_for_portfolio` dispositions.
- Added idempotent as-of rule evaluation over immutable price datasets, durable
  unique alerts, and append-only human acknowledgements with derived status.
- Added CLI workflows for monitor creation, evaluation, alert listing, and
  acknowledgement; the regression suite now covers the complete lifecycle.
- Accepted the Milestone 4 signal-quality experiment and product contract with
  restart reconstruction, explicit known limitations, and no automation or
  execution integration.
- Accepted ADR-0014 and recorded the Milestone 5 research-refresh review
  contract and fidelity experiment.
- Added immutable, idempotent same-company research reviews gated by complete
  canonical memos and strictly increasing `as_of` boundaries.
- Added exact-period claim inventories, period-labeled latest-metric deltas,
  normalized limitation changes, memo-section hashes, and time-bounded linked
  alert evidence.
- Added review retrieval and append-only human outcomes without mutating source
  research, alerts, dispositions, monitors, portfolios, or external systems.
- Accepted the Milestone 5 fidelity experiment and product contract with full
  delta-category truth tables, temporal alert boundaries, restart
  reconstruction, and explicit known limitations.
- Accepted ADR-0015 for a loopback-only dashboard that reuses the existing
  research and human-decision services without adding authority.
- Added a dependency-free loopback HTTP server, secret-safe configuration API,
  saved-run list/detail reconstruction, company-research endpoint, and guarded
  human-disposition endpoint.
- Added a responsive same-origin dashboard for research initiation, memo and
  limitation review, telemetry, saved-run navigation, and human disposition.
- Browser-verified the dashboard against the real research database at desktop
  and mobile widths and accepted its 110-test security and lifecycle audit.
- Accepted ADR-0016 and recorded the Milestone 6 unified-workspace contract and
  usability experiment.
- Added exact-byte browser uploads and list/reconstruction methods for price
  datasets, monitors, alerts, and research reviews.
- Added guarded dashboard APIs for screening, hypothetical portfolio analysis,
  backtesting, monitor evaluation, alert acknowledgement, and research reviews.
- Added responsive Quant lab, Monitoring, Alert ledger, and Reviews workspaces
  while retaining the Research workflow and existing domain validation.
- Accepted the Milestone 6 usability experiment after 115 tests, full HTTP
  lifecycle coverage, real-database browser verification, mobile containment,
  and zero browser console errors.
- Recorded the conversational research operator as a deferred product
  requirement pending measured value and stable tool contracts.
- Accepted ADR-0017 and recorded the Milestone 7 quarterly-period-integrity
  contract and experiment.
- Added explicit annual 10-K or quarterly 10-Q selection to the CLI and
  dashboard while retaining annual research as the default.
- Added discrete-quarter, year-to-date, and instant SEC fact selection with
  exact-period calculations and same-form cross-filing revision audits.
- Prevented quarterly annualization and DCF generation, added explicit annual
  evidence-refresh limitations, and updated the analysis prompt to version 2.2.
- Accepted Milestone 7 after 118 passing tests and a read-only live Apple 10-Q
  extraction for accession `0000320193-26-000013` with correct period shapes.
- Accepted ADR-0018 and defined Milestone 8 around cognitive-load reduction;
  future portfolio and comparison visualizations remain a measured backlog.
- Reduced primary dashboard navigation from four choices to Research and
  Reviews, with Quant and Monitoring retained under a Tools disclosure.
- Converted seven advanced workflows into question-led disclosures with zero
  forms expanded by default and at most one open per workspace.
- Moved the human checkpoint directly after thesis and known limitations while
  preserving the full memo and model metadata in a secondary disclosure.
- Accepted Milestone 8 after 120 passing tests, real-database desktop/mobile
  browser verification, mobile containment, and zero browser console errors.
- Accepted ADR-0019 and defined Milestone 9 as an append-only research-quality
  evaluation ledger that does not use stock performance or an LLM judge.
- Added five reproducible integrity gates covering artifacts, claim lineage,
  visible evidence gaps, provenance, and preserved human authority.
- Added six validated human rubric scores with required rationales and derived
  acceptance using the versioned 9-of-12 threshold.
- Persisted append-only evaluations with prompt, model, schema, token, latency,
  actor, gate, score, and rationale context plus CLI create/list workflows.
- Added a progressive-disclosure dashboard rubric and expandable evaluation
  ledger without adding model calls, market outcomes, or execution authority.
- Accepted Milestone 9 after 128 passing tests, restart reconstruction,
  real-database desktop/mobile browser verification, and zero console errors.
- Added explicit Quant and Monitoring prerequisite guidance after operator
  testing showed that collapsed forms with no eligible artifacts looked empty.
- Accepted ADR-0020 and refined Milestone 10 as a read-only market-data provider
  boundary with Alpaca optional, immutable persistence, and no trading-client
  capability.
- Accepted ADR-0021 for Robinhood MCP: use it as read-only portfolio context
  before any execution capability, with a separate ADR required before orders,
  day trading, recurring-buy changes, or rebalancing automation.

## Accepted decisions

- ADR-0001: Preserve human authority over investment and execution decisions.
- ADR-0002: Maintain persistent project state and session logs.
- ADR-0003: Scope version one as a U.S. equities research copilot.
- ADR-0004: Use structured memos with claim-level evidence.
- ADR-0005: Adopt a primary-source-first evidence policy.
- ADR-0006: Use a deterministic, resumable research workflow.
- ADR-0007: Use a Python 3.12 local-first implementation stack.
- ADR-0008: Use OpenAI Responses with structured analysis output.
- ADR-0009: Preserve filing context in multi-period comparisons and revisions.
- ADR-0010: Require measured evidence before adopting additional complexity.
- ADR-0011: Scope version two as a complete research decision record.
- ADR-0012: Scope Milestone 3 as a point-in-time quantitative lab.
- ADR-0013: Scope Milestone 4 as deterministic decision monitoring.
- ADR-0014: Scope Milestone 5 as research-refresh reviews.
- ADR-0015: Add a loopback-only local dashboard.
- ADR-0016: Scope Milestone 6 as a unified operator workspace.
- ADR-0017: Scope Milestone 7 as period-safe quarterly research updates.
- ADR-0018: Scope Milestone 8 as dashboard cognitive-load reduction.
- ADR-0019: Scope Milestone 9 as a research-quality evaluation ledger.
- ADR-0020: Scope Milestone 10 as automatic read-only market data.
- ADR-0021: Robinhood portfolio context first; only the user-designated Agentic
  account is in scope for potential confirmed orders. Other accounts are for
  research insights and recommendations only.

## Open questions

- Which materiality threshold should trigger narrative review of a detected
  cross-filing revision?
- Which of the available Robinhood read tools belong in the app's future
  portfolio-snapshot contract, and how will the app obtain authorized access?
- Which private remote destination should hold the repository backup?

## Blockers

None for the documented local workflow. Docker image execution
remains a non-blocking environment follow-up because the local daemon previously
stalled while resolving image metadata.

## Next actions

1. Resolve P11-02: supported authorization/transport for read-only snapshots.
2. Wire snapshot/refresh persistence into an interruption-safe collection service
   and add saved research links. Refresh records and deterministic calculations
   pass synthetic tests; live transport and dashboard wiring remain pending.
3. Keep Experiment 0009 pending until its operator acceptance is documented;
   paid market data remains optional and CSV import remains available.
4. Configure a private Git remote once the user supplies a destination; do not
   treat local commits as an off-device backup.

## Future integration note

`../diveTrader` is a separate Alpaca execution prototype. See
`docs/architecture/dive-trader-integration-note.md`. It is not part of version
one and must not receive research-to-broker integration without a separate ADR,
canonical API cleanup, order-intent approval boundary, risk controls, audit,
idempotency, and reconciliation.

## Resume here

Read the progress table above and the latest session log. The next development
step is P11-02 in `docs/milestone-11.md`, not rebuilding the committed provider.
Robinhood tools are available in this chat, but application integration is not
implemented. Preserve ADR-0021 and the user's account scope. Keep sensitive
portfolio data and account identifiers out of Git.
