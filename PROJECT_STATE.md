# Project State

Last updated: 2026-07-01

Session status: Milestone 3 active

## Current phase

Milestone 3 point-in-time quantitative lab.

## Active objective

Implement ADR-0012 and the Milestone 3 product contract.

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

## Open questions

- Which materiality threshold should trigger narrative review of a detected
  cross-filing revision?

## Blockers

None for the documented Version 2 local workflow. Docker image execution
remains a non-blocking environment follow-up because the local daemon previously
stalled while resolving image metadata.

## Next actions

1. Select the next product goal; do not expand into execution without a separate
   accepted architecture decision and safety contract.

## Future integration note

`../diveTrader` is a separate Alpaca execution prototype. See
`docs/architecture/dive-trader-integration-note.md`. It is not part of version
one and must not receive research-to-broker integration without a separate ADR,
canonical API cleanup, order-intent approval boundary, risk controls, audit,
idempotency, and reconciliation.

## Resume here

Milestone 3 is complete. Begin the next session by selecting and recording the
next product goal. Keep DiveTrader separate and execution out of scope unless a
new ADR defines the approval, risk, audit, idempotency, and reconciliation
boundaries.
