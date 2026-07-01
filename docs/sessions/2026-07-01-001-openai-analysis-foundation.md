# Session: OpenAI analysis foundation

- Date: 2026-07-01
- Status: Active

## Objective

Persist structured model analysis artifacts and run the first live OpenAI
evaluation against the retained Apple financial claims.

## Outcomes

- Verified `OPENAI_API_KEY` is correctly formatted and Git-ignored without
  displaying it.
- Added analysis artifact and input-claim lineage ORM models.
- Added Alembic migration `20260701_0004`.
- Added an analysis repository and CLI command.
- Defined Financial Analysis Evaluation Rubric v1.
- Attempted the first live request; OpenAI returned `insufficient_quota` before
  generation, and no artifact was persisted.
- After billing was updated, the retry succeeded and persisted the first
  structured Apple financial analysis.
- The artifact passed all gates and scored 11/12 under the v1 rubric.
- Prompt version 1.1 addresses the two observed evidence-fidelity issues.
- Added a one-command company research orchestrator, configuration doctor, and
  user guide.
- Live-validated the one-command workflow against Walmart. The first attempt
  exposed a missing issuer concept; the corrected run persisted successfully.
- Prompt v1.1 scored 12/12 on Walmart.
- Added evidence-gap persistence in migration `20260701_0005`.
- Added and live-validated `research-company`, `list-runs`, `show-run`, and
  secret-safe `doctor` commands.
- Added the repository README and user guide.

## Validation

- 46 tests pass, including orchestration, evidence-gap, and saved-run views.
- Formatting, lint, migration, persistence, and cross-run lineage checks pass.

## Handoff

Expand deterministic financial evidence before treating the financial-analysis
stage as complete. The user-facing CLI workflow is now operational.
