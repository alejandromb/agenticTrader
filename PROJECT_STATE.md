# Project State

Last updated: 2026-07-01

Session status: Active

## Current phase

Architecture and project foundation.

## Active objective

Complete the first live OpenAI financial-analysis evaluation after API quota is
available.

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

- Does the first live artifact meet the v1 rubric, and which observed failures
  require prompt or contract changes?

## Blockers

Docker and Compose configuration validation passes. Full image execution remains
to be verified because the local Docker daemon stalled while resolving image
metadata, including for an already cached base image.

The first live request reached OpenAI but returned `insufficient_quota`. Billing
or API credits must be enabled before the evaluation can complete. No analysis
artifact was created from the failed request.

## Next actions

1. Enable OpenAI API billing or credits for the configured project key.
2. Retry the pinned-model Apple analysis.
3. Score the result with Financial Analysis Evaluation Rubric v1.
4. Record the evaluation and revise the prompt only from observed failures.

## Resume here

First, confirm API quota is available, then retry `analyze-financials` against
the retained Apple run. Evaluate the saved artifact with
`docs/evaluation/financial-analysis-v1.md`. Never display or persist the key.

## Working-tree note

The foundation session is checkpointed through `651b7d4`. The current analysis
artifact work is pending its session checkpoint commit.
