# Investment Memo Contract

This document explains the version-one memo contract. The machine-validatable
definition is `schemas/investment-memo-v1.schema.json`.

## Required memo sections

| Section | Purpose |
| --- | --- |
| Identity | Memo ID, schema version, creation time, and analysis as-of time |
| Subject | Ticker, legal company name, exchange, and security identifier when available |
| Question | The specific investment question and analysis horizon |
| Executive view | Concise thesis, counter-thesis, and current conclusion |
| Business | Business model, segments, economics, and competitive position |
| Financials | Material historical performance, balance-sheet condition, and cash generation |
| Valuation | Method, inputs, ranges, and sensitivity—not a false-precision price target |
| Risks | Company, industry, financial, regulatory, and thesis-specific failure modes |
| Uncertainties | Missing, stale, conflicting, or low-confidence information |
| Claims | Typed assertions referenced throughout the memo |
| Evidence | Captured support for factual claims |
| Disposition | Human-owned workflow state and optional rationale |

## Claim rules

### Fact

A fact must cite one or more evidence records. Conflicting sources are retained
and the conflict is disclosed; the system does not silently choose one.

### Calculation

A calculation identifies its input claims, formula or method, result, units,
and reproducibility notes. Inputs that originate externally must themselves be
evidenced facts.

### Assumption

An assumption states why it is being used, its plausible range when applicable,
and which conclusions depend on it.

### Opinion

An opinion states its rationale and should reference the facts, calculations,
or assumptions that informed it. A confidence label is not evidence.

## Evidence rules

Evidence records contain:

- a stable internal evidence ID;
- source title, publisher, source type, and canonical URL;
- publication and retrieval timestamps when available;
- a source location such as page, table, filing section, or paragraph;
- a short excerpt or normalized value supporting the claim; and
- capture metadata sufficient to detect or explain later source changes.

A URL alone is not sufficient evidence. Search-result snippets are discovery
tools and must not be used as final evidence.

## Time semantics

`as_of` defines the information boundary for an analysis. The memo must not use
information published after this time unless explicitly marked as a later
review. This prevents hindsight leakage when evaluating historical decisions.

## Human disposition

The allowed states are:

- `undecided`
- `investigate`
- `watch`
- `reject`
- `consider_for_portfolio`

Only the human user can set a state other than `undecided`. Agent output may
recommend a disposition but cannot record it as the human decision.
