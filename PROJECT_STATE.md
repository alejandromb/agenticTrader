# Project State

Last updated: 2026-06-30

Session status: Active

## Current phase

Architecture and project foundation.

## Active objective

Implement durable SQLite workflow state and append-only transition history.

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

None.

## Next actions

1. Implement durable workflow state and transition history in SQLite.
2. Add a command-line entry point for memo validation and SEC discovery.
3. Implement evidence artifact metadata and content hashing.
4. Run an identified live SEC discovery request.

## Resume here

Start by deciding how research steps are orchestrated. Prefer the smallest model
that preserves deterministic state transitions, evidence provenance, and
independent challenge of the thesis.

## Working-tree note

The repository was initialized during the foundation session. See the latest
session log and Git status for the authoritative commit state.
