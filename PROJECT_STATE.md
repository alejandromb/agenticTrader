# Project State

Last updated: 2026-06-30

Session status: Paused at a clean handoff point

## Current phase

Architecture and project foundation.

## Active objective

Create a representative memo fixture and define the first accepted source types
and acquisition policy.

## Completed

- Captured the project vision in `Agentic_Trading_Project_Summary.md`.
- Established that AI is advisory and humans retain investment and execution
  authority in ADR-0001.
- Established persistent project state and session logging in ADR-0002.
- Scoped version one as a U.S. equities research copilot in ADR-0003.
- Defined structured investment memos and claim-level evidence in ADR-0004.

## Accepted decisions

- ADR-0001: Preserve human authority over investment and execution decisions.
- ADR-0002: Maintain persistent project state and session logs.
- ADR-0003: Scope version one as a U.S. equities research copilot.
- ADR-0004: Use structured memos with claim-level evidence.

## Open questions

- Which public source types should version one accept?
- What evidence capture and retention guarantees are practical for version one?
- Which company should be used for the first representative memo fixture?

## Blockers

None.

## Next actions

1. Create a representative example and validation fixture.
2. Decide the first source types and acquisition policy.
3. Decide the initial orchestration model.
4. Select the implementation stack.

## Resume here

Start by creating one realistic investment memo fixture against
`schemas/investment-memo-v1.schema.json`. Use it to expose weaknesses in the
contract before making technology or orchestration decisions. The company used
for the fixture has not been selected.

## Working-tree note

The repository was initialized during the foundation session. See the latest
session log and Git status for the authoritative commit state.
