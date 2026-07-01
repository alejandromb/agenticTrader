# ADR-0002: Maintain persistent project state and session logs

- Status: Accepted
- Date: 2026-06-30

## Context

Development may be interrupted or resumed in a new conversation without full
access to prior conversational context. Git records file changes but does not,
by itself, preserve the current objective, unresolved questions, or the precise
next action.

The project needs a small, durable handoff mechanism that allows a human or AI
collaborator to resume work from repository contents alone.

## Decision

The repository will maintain two complementary records:

1. `PROJECT_STATE.md` is the canonical current-state snapshot. It records the
   active objective, completed work, decisions, open questions, blockers, and
   next actions. It is updated whenever those facts change and before ending a
   meaningful work session.
2. `docs/sessions/` contains append-only session logs. Each meaningful session
   records its scope, outcomes, files changed, validation performed, and handoff
   notes.

At the start of a resumed session, collaborators should read, in order:

1. `PROJECT_STATE.md`;
2. the latest session log when more detail is needed;
3. applicable ADRs and source files.

Session logs use the filename format `YYYY-MM-DD-NNN-short-description.md`,
where `NNN` distinguishes multiple sessions on the same date.

Project state must contain facts rather than raw conversational transcripts.
Secrets, credentials, private financial information, and unnecessarily
sensitive account data must never be included.

## Consequences

- Work can resume without relying on chat history.
- The current state remains quick to read, while detailed history remains
  available when needed.
- Some information overlaps with Git history, but the session log captures
  intent and validation that a diff cannot reliably express.
- Every meaningful session has a small documentation cost.
- `PROJECT_STATE.md` must be kept current or it will become misleading.

## Alternatives considered

### Rely only on Git history

Rejected because commits do not reliably communicate pending work, blockers,
or the next intended action.

### Store complete conversation transcripts

Rejected because transcripts are noisy, may contain sensitive data, and are
slow to use as a handoff artifact.

### Maintain only session logs

Rejected because resuming work would require reconstructing the current state
from an ever-growing history.
