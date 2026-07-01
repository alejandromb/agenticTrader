# Version 2 Product Contract

## Outcome

Turn the accepted Version 1 financial research run into a complete, retrievable
investment decision record for one U.S. public company.

## Required artifacts

- captured primary-source business and risk evidence;
- structured business-quality analysis;
- structured material-risk analysis;
- deterministic valuation scenarios and sensitivity;
- bull, base, and bear cases;
- devil's-advocate challenge;
- canonical investment memo;
- known limitations;
- model, prompt, source, claim, calculation, and assumption lineage; and
- a separate human disposition event.

## Required commands

```text
research-company TICKER --question QUESTION
show-run RUN_ID
record-disposition RUN_ID DISPOSITION [--rationale TEXT]
```

The research command must not set a disposition. The disposition command must
not rewrite evidence, analysis, valuation, or memo content.

## Quality gates

- No unknown or cross-run claim references.
- No valuation without explicit assumptions and an `as_of` boundary.
- No single scenario represented as certain fair value.
- No missing evidence gap omitted from known limitations.
- No model-owned human disposition.
- No trade instruction, position size, order, or broker call.
- Full saved-run reconstruction after process restart.

## Explicit non-goals

Screeners, portfolio analytics, backtesting, alerts, automation, and execution
are not Version 2 deliverables.
