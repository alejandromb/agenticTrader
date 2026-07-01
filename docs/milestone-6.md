# Milestone 6 Product Contract

## Outcome

Make every accepted research, quantitative, monitoring, and refresh-review
workflow operable from the loopback dashboard without weakening lineage or human
authority.

## Dashboard workspaces

### Research

- Start company research.
- Browse canonical memos, limitations, cases, risks, valuation, and telemetry.
- Record an eligible human disposition.

### Quant lab

- Import immutable adjusted-price CSV bytes with provenance.
- Run deterministic memo-backed screens.
- Analyze hypothetical `ticker,shares` holdings.
- Run versioned moving-average backtests with explicit costs.

### Monitoring

- Create typed human-defined rules from an eligible completed run.
- Evaluate rules against a selected immutable dataset and `as_of` date.
- List open/acknowledged alerts and append a human acknowledgement.

### Research reviews

- Compare an eligible baseline/current run pair.
- Inspect claim, metric, limitation, section, and linked-alert deltas.
- Record one append-only human outcome.

## Invariants

- All state-changing requests use the dashboard request token.
- Uploaded files preserve exact bytes and are size-bounded.
- Dataset, run, monitor, alert, review, and strategy identities remain visible.
- Domain errors remain explicit and do not produce partial substitute results.
- No operation creates an order, changes a portfolio, contacts a broker, or
  grants a model human authority.

## Non-goals

No live feeds, scheduled automation, remote hosting, notification delivery,
collaboration, parameter optimization, or execution integration.
