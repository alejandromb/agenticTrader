# Project State

Last updated: 2026-07-01

Session status: Active

## Current phase

Architecture and project foundation.

## Active objective

Validate cash-allocation analysis and begin multi-period financial comparisons.

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

## Accepted decisions

- ADR-0001: Preserve human authority over investment and execution decisions.
- ADR-0002: Maintain persistent project state and session logs.
- ADR-0003: Scope version one as a U.S. equities research copilot.
- ADR-0004: Use structured memos with claim-level evidence.
- ADR-0005: Adopt a primary-source-first evidence policy.
- ADR-0006: Use a deterministic, resumable research workflow.
- ADR-0007: Use a Python 3.12 local-first implementation stack.
- ADR-0008: Use OpenAI Responses with structured analysis output.

## Open questions

- How should comparable prior periods be represented without confusing facts
  from the current filing with facts restated in later filings?

## Blockers

Docker and Compose configuration validation passes. Full image execution remains
to be verified because the local Docker daemon stalled while resolving image
metadata, including for an already cached base image.

## Next actions

1. Validate prompt version 1.3 and cash allocation on a live research run.
2. Extract filing narrative explaining the purpose of material capital spending.
3. Design multi-period fact identity and restatement handling.
4. Add prior-year comparisons to the financial analysis contract.
5. Validate the Docker image when the local daemon can resolve image metadata.

## Resume here

Start by designing multi-period and restatement semantics, then validate prompt
v1.2 on a fresh run. Never display or persist the API key.

## Working-tree note

The Apple evaluation is checkpointed through `a062e52`. The Walmart evaluation,
one-command workflow, evidence-gap persistence, and saved-run views are pending
the next commit.
