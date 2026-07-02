# ADR-0019: Scope Milestone 9 as a research-quality evaluation ledger

- Status: Accepted
- Date: 2026-07-02

## Context

The project records prompt versions, evidence, limitations, model usage, and
human dispositions, but it cannot yet answer whether a research-system change
improved the quality of the decision record. Subsequent price performance is not
a valid substitute: a sound process can precede a poor outcome and weak reasoning
can precede a favorable one.

## Decision

Milestone 9 will add immutable research-quality evaluations tied to one saved
research run and rubric version. Each evaluation combines:

1. deterministic integrity gates computed from persisted artifacts;
2. six human-scored criteria from 0 to 2 with required rationales;
3. the evaluated prompt/model/schema provenance and usage telemetry;
4. an explicit accepted/rejected result using a versioned threshold; and
5. append-only persistence so later system changes cannot rewrite prior scores.

The initial rubric evaluates numerical fidelity, evidence fidelity,
fact/judgment separation, balance, uncertainty, and decision usefulness. A run
passes only when every automatic gate passes, no criterion scores zero, and the
total is at least 9 of 12.

Evaluations measure research-process quality. They do not measure alpha, predict
returns, recommend securities, or authorize portfolio action.

## Acceptance criteria

- Automatic gates are reproducible from the saved run after restart.
- Missing or inconsistent lineage and limitation coverage fail visibly.
- Scores outside 0–2 and incomplete rationales are rejected.
- The acceptance result is derived, not user-selected.
- Evaluations retain rubric, prompt, model, schema, token, and latency context.
- CLI and dashboard can create and inspect evaluations without another model call.
- Tests prove append-only history and unchanged research/disposition authority.

## Explicit exclusions

- stock-price outcome scoring or backfilled performance attribution;
- automatic LLM-as-judge scoring;
- ranking analysts, models, companies, or investment attractiveness;
- sentiment, new data providers, or additional model calls; and
- portfolio construction, brokerage, or execution.
