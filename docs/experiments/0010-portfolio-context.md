# Experiment 0010: Portfolio context with less navigation

- Status: Planned; not executed
- Baseline: Manually reconstructing holdings context alongside saved research

## Hypothesis

A durable account snapshot linked to saved research lets the user inspect
exposure and evidence with fewer manual steps and no loss of provenance.

## Deterministic acceptance

Use synthetic holdings: AAA 10 shares at a quote of 20, BBB 5 at 40.
Expected values are 200 each, total priced equities 400, weights 50% each.
With broker account value 500 and cash 100, account weights are 40% each.
With AAA average cost 15, its estimated unrealized result is 50.

Require tests for missing cost, missing quote, zero denominator, negative/boxed
positions, unsupported currency, other asset classes, pagination failure,
duplicate positions, mismatched quote timestamps, and unavailable margin data.
Unknown values must remain unknown and incomplete collection must remain visible.

Require immutable reload after process restart, retained refresh timestamps,
idempotent content reuse, explicit failed refresh, account isolation, and exact
saved memo links without modifying source research. Verify that mock credential
sentinels and broker identifiers never enter public responses or tracked files.

## Operator acceptance

With an authorized connection, on desktop and narrow mobile layout:

1. Select an account and refresh with zero exported/imported files.
2. See freshness, coverage, account value, cash and buying power distinctly.
3. Open an existing holding's research in one action from the holdings list.
4. Navigate away and reload; the same account, snapshot and ticker remain selected.
5. Disconnect the provider and refresh; retain the prior snapshot with visible
   failure/staleness, never a false zero balance or silent fallback to another account.

Record observed steps, task completion time, errors, operator feedback, tested
commit, and actual validation results. Require zero manual file transfers, one
action to saved research, passing integrity checks, and operator confirmation
that context is understandable. Timing has no claimed improvement until measured.
Do not store real balances, holdings, identifiers, or screenshots in Git.

Fixture success alone does not accept the milestone. No stock-return claim or
additional LLM call is part of this experiment.
