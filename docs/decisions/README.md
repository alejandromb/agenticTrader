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
| [0008](0008-openai-structured-analysis-adapter.md) | Use OpenAI Responses with structured analysis output | Accepted |
| [0009](0009-multi-period-and-restatement-semantics.md) | Preserve filing context in multi-period comparisons | Accepted |
| [0010](0010-evidence-before-complexity.md) | Require evidence before adopting additional complexity | Accepted |
| [0011](0011-version-two-research-decision-record.md) | Scope version two as a complete research decision record | Accepted |
| [0012](0012-milestone-three-quantitative-lab.md) | Scope Milestone 3 as a point-in-time quantitative lab | Accepted |
| [0013](0013-milestone-four-decision-monitoring.md) | Scope Milestone 4 as deterministic decision monitoring | Accepted |
| [0014](0014-milestone-five-research-refresh-reviews.md) | Scope Milestone 5 as research-refresh reviews | Accepted |
| [0015](0015-local-dashboard-surface.md) | Add a loopback-only local dashboard | Accepted |
| [0016](0016-milestone-six-unified-operator-workspace.md) | Scope Milestone 6 as a unified operator workspace | Accepted |
| [0017](0017-milestone-seven-quarterly-research-updates.md) | Scope Milestone 7 as period-safe quarterly research updates | Accepted |
| [0018](0018-milestone-eight-cognitive-load.md) | Scope Milestone 8 as dashboard cognitive-load reduction | Accepted |
| [0019](0019-milestone-nine-research-quality-ledger.md) | Scope Milestone 9 as a research-quality evaluation ledger | Accepted |

## Convention

Use sequential four-digit identifiers. A later ADR supersedes an accepted
decision instead of rewriting its history.
