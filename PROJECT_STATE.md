# Project State

Last updated: 2026-06-30

Session status: Active

## Current phase

Architecture and project foundation.

## Active objective

Complete live SEC filing capture using an identifying contact in the User-Agent.

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
- Added a CLI for memo validation, SEC discovery, and workflow state operations.
- Added content-addressed local artifact storage with integrity verification.
- Verified live Apple filing discovery against SEC submissions data.

## Accepted decisions

- ADR-0001: Preserve human authority over investment and execution decisions.
- ADR-0002: Maintain persistent project state and session logs.
- ADR-0003: Scope version one as a U.S. equities research copilot.
- ADR-0004: Use structured memos with claim-level evidence.
- ADR-0005: Adopt a primary-source-first evidence policy.
- ADR-0006: Use a deterministic, resumable research workflow.
- ADR-0007: Use a Python 3.12 local-first implementation stack.

## Open questions

- What minimum evidence artifact should the SEC collector persist first?
- Which model provider, if any, should power the first extraction experiment?

## Blockers

The SEC submissions endpoint accepts the `AgenticTrading/0.1` User-Agent, but
the SEC Archives filing endpoint returned HTTP 403. A real contact identifier
must be added to `SEC_USER_AGENT` before retrying live document capture.

## Next actions

1. Configure `SEC_USER_AGENT` with the project name, version, and owner contact.
2. Retry live SEC filing capture and verify its stored SHA-256.
3. Persist evidence metadata alongside captured artifacts.
4. Implement deterministic extraction of filing metadata and selected facts.

## Resume here

Start by configuring the SEC identifying contact and rerunning
`sec-fetch-latest`. Do not store the contact value in Git; provide it through
the `SEC_USER_AGENT` environment variable.

## Working-tree note

The repository was initialized during the foundation session. See the latest
session log and Git status for the authoritative commit state.
