# Project State

Last updated: 2026-07-01

Session status: Active

## Current phase

Architecture and project foundation.

## Active objective

Surface revision audits and explicit analysis limitations.

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

## Open questions

- Which materiality threshold should trigger narrative review of a detected
  cross-filing revision?

## Blockers

Docker and Compose configuration validation passes. Full image execution remains
to be verified because the local Docker daemon stalled while resolving image
metadata, including for an already cached base image.

## Next actions

1. Persist calculation claims with formula and input-claim lineage.
2. Feed validated calculation claims into financial analysis.
3. Add capital-allocation detail extraction from filing tables.
4. Validate automatic revision auditing on an issuer with a known revision.

## Future integration note

`../diveTrader` is a separate Alpaca execution prototype. See
`docs/architecture/dive-trader-integration-note.md`. It is not part of version
one and must not receive research-to-broker integration without a separate ADR,
canonical API cleanup, order-intent approval boundary, risk controls, audit,
idempotency, and reconciliation.

## Resume here

Live-validate revision audits, then implement deterministic growth calculations.
Keep version one limited to research; never display or persist the API key.
