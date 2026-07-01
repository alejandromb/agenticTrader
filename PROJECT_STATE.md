# Project State

Last updated: 2026-06-30

Session status: Active

## Current phase

Architecture and project foundation.

## Active objective

Implement deterministic extraction of selected SEC filing facts into typed,
evidence-linked candidate claims.

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

## Accepted decisions

- ADR-0001: Preserve human authority over investment and execution decisions.
- ADR-0002: Maintain persistent project state and session logs.
- ADR-0003: Scope version one as a U.S. equities research copilot.
- ADR-0004: Use structured memos with claim-level evidence.
- ADR-0005: Adopt a primary-source-first evidence policy.
- ADR-0006: Use a deterministic, resumable research workflow.
- ADR-0007: Use a Python 3.12 local-first implementation stack.

## Open questions

- Which model provider, if any, should power the first extraction experiment?

## Blockers

Docker and Compose configuration validation passes. Full image execution remains
to be verified because the local Docker daemon stalled while resolving image
metadata, including for an already cached base image.

## Next actions

1. Convert selected XBRL facts into typed candidate claims with source links.
2. Persist candidate claims and extraction lineage.
3. Add validation that facts cannot reference sources from another run.
4. Expand deterministic extraction to the minimum financial statement set.

## Resume here

Start by defining and implementing the candidate-claim persistence model. A
fact must retain taxonomy, concept, unit, period, accession, and source-document
lineage. Keep the SEC contact in `SEC_USER_AGENT`; never persist it.

## Working-tree note

The repository was initialized during the foundation session. See the latest
session log and Git status for the authoritative commit state.
