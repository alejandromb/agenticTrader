# Session: Project foundation

- Date: 2026-06-30
- Status: Complete

## Objective

Establish the project direction, its first authority boundary, and a durable
way to resume work after an interruption.

## Outcomes

- Reviewed the Agentic Trading project summary.
- Confirmed the platform is an AI-assisted investment operating system rather
  than an autonomous trader.
- Established human authority over capital allocation and brokerage actions.
- Established a persistent project-state and session-log convention.
- Scoped version one as a research copilot for long-term fundamental analysis
  of U.S. publicly traded equities.
- Defined the structured investment-memo and claim-level evidence contracts.
- Created an Apple fiscal 2025 memo fixture and refined the schema from it.
- Adopted a primary-source-first evidence and acquisition policy.
- Adopted a deterministic, resumable research workflow.
- Selected and scaffolded the Python 3.12 local-first stack.
- Implemented tested memo validation and SEC filing discovery.
- Implemented durable SQLite workflow state and append-only transitions.
- Added the local CLI and content-addressed artifact storage.
- Verified live SEC filing discovery. Live document retrieval returned HTTP 403
  without a real owner contact in the User-Agent.

## Decisions

- ADR-0001: Preserve human authority over investment and execution decisions.
- ADR-0002: Maintain persistent project state and session logs.
- ADR-0003: Scope version one as a U.S. equities research copilot.
- ADR-0004: Use structured memos with claim-level evidence.
- ADR-0005: Adopt a primary-source-first evidence policy.
- ADR-0006: Use a deterministic, resumable research workflow.
- ADR-0007: Use a Python 3.12 local-first implementation stack.

## Files added or updated

- `PROJECT_STATE.md`
- `docs/decisions/README.md`
- `docs/decisions/0001-human-authority-over-investment-and-execution.md`
- `docs/decisions/0002-persistent-project-state-and-session-logs.md`
- `docs/decisions/0003-v1-research-copilot-scope.md`
- `docs/decisions/0004-structured-memos-and-claim-level-evidence.md`
- `docs/contracts/investment-memo.md`
- `schemas/investment-memo-v1.schema.json`
- `examples/investment-memos/aapl-2025-example.json`
- `docs/decisions/0005-source-quality-and-acquisition-policy.md`
- `docs/contracts/source-policy.md`
- `docs/decisions/0006-deterministic-research-workflow.md`
- `docs/contracts/research-workflow.md`
- `docs/decisions/0007-python-local-first-stack.md`
- `pyproject.toml`
- `src/agentic_trading/validation.py`
- `src/agentic_trading/sec.py`
- `tests/test_validation.py`
- `tests/test_sec.py`
- `src/agentic_trading/workflow.py`
- `src/agentic_trading/repository.py`
- `src/agentic_trading/cli.py`
- `src/agentic_trading/artifacts.py`
- `tests/test_repository.py`
- `tests/test_cli.py`
- `tests/test_artifacts.py`
- `docs/sessions/README.md`
- `docs/sessions/2026-06-30-001-project-foundation.md`

## Validation

- Reviewed the Markdown content for internal consistency.
- Ran `git diff --check` to detect whitespace errors.
- Parsed the investment-memo JSON Schema successfully with `jq`.

## Unresolved questions

- What identifying contact should be used for live SEC requests?

## Handoff

Next, configure a real contact in `SEC_USER_AGENT`, retry live filing capture,
and then persist evidence metadata alongside the content-addressed artifact.
