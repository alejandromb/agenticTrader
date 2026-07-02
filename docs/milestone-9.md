# Milestone 9 Product Contract

## Outcome

Create a durable feedback loop for determining whether research-system changes
improve evidence integrity and decision usefulness.

## Evaluation workflow

1. Select a saved run with a canonical memo and analysis artifact.
2. Recompute deterministic integrity gates from persisted data.
3. Score six human criteria from 0 to 2 and provide a rationale for each.
4. Persist the complete evaluation with artifact provenance and telemetry.
5. Derive acceptance: all gates pass, no zero score, total at least 9 of 12.
6. Review evaluation history without altering the research run or disposition.

## Automatic gates

- canonical analysis and memo artifacts exist;
- every cited analysis claim belongs to the run and its recorded model input;
- every persisted evidence gap appears in the canonical memo limitations;
- model, prompt, response, and schema provenance is present; and
- the immutable memo retains an undecided human-disposition placeholder.

## Human criteria

- numerical fidelity;
- evidence fidelity;
- fact/judgment separation;
- balance;
- uncertainty; and
- decision usefulness.

## Boundaries

This evaluates the research artifact, not the company and not later returns.
It creates no model call and grants no investment or execution authority.

## Acceptance

Accepted on 2026-07-02 with 128 passing tests, restart reconstruction,
append-only history, exact CLI/dashboard payload coverage, real-database browser
verification, mobile containment, and zero browser console errors. See
`docs/experiments/0008-research-quality-ledger.md`.
