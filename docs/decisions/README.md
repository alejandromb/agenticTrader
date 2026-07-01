# Architecture Decision Records

Architecture Decision Records (ADRs) capture consequential choices that shape
the system. They explain the context, the chosen direction, and its tradeoffs.

## Status meanings

- **Proposed:** Under discussion and not yet binding.
- **Accepted:** The current architectural direction.
- **Superseded:** Replaced by a later ADR.
- **Rejected:** Considered but not adopted.

## Decisions

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](0001-human-authority-over-investment-and-execution.md) | Preserve human authority over investment and execution decisions | Accepted |
| [0002](0002-persistent-project-state-and-session-logs.md) | Maintain persistent project state and session logs | Accepted |
| [0003](0003-v1-research-copilot-scope.md) | Scope version one as a U.S. equities research copilot | Accepted |
| [0004](0004-structured-memos-and-claim-level-evidence.md) | Use structured memos with claim-level evidence | Accepted |
| [0005](0005-source-quality-and-acquisition-policy.md) | Adopt a primary-source-first evidence policy | Accepted |
| [0006](0006-deterministic-research-workflow.md) | Use a deterministic, resumable research workflow | Accepted |
| [0007](0007-python-local-first-stack.md) | Use a Python 3.12 local-first implementation stack | Accepted |

## Convention

Use sequential four-digit identifiers. A later ADR supersedes an accepted
decision instead of rewriting its history.
