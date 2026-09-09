# Manual account loss reviews

Run a validated local JSON checkpoint:

```sh
.venv/bin/python -m agentic_trading.account_risk private-check.json
```

The command saves input and deterministic output together in the existing
content-addressed artifact store. It prints the hash and review result. It does
not connect to a broker, send notifications, schedule jobs or create orders.

Required input fields: policy (opaque account_ref UUID, baseline_at,
baseline_value, warning_loss, review_loss, optional max_age_seconds default 900),
matching account_ref, observed_at, evaluated_at, account_value. Optional source_at
and flows_verified_through must be explicit aware timestamps when verified.
cash_flows is a list of event_id, occurred_at and signed amount: external deposits
positive and withdrawals negative. All values are USD. Keep inputs private.

Formula: account value - baseline value - net external funding since baseline.
Fees and investment income remain in performance; internal buys/sells are not
external flows. This is a dollar loss budget, not time-weighted return, not a
percentage performance comparison, and not a trailing high-watermark rule.

Results are below_threshold, warning, review, or needs_data. Missing valuation
time, stale valuations, or unverified flow coverage produce needs_data with a
clearly provisional arithmetic level. Retrieval time cannot replace valuation
time. Negative account values can trigger review. Duplicate event IDs and
cross-account inputs fail validation. Exact threshold equality triggers the
corresponding level. A review is not an instruction to liquidate.

Limits: no authoritative transfer collector, managed benchmark reconciliation,
dashboard integration, ORM review index, calendar-aware freshness, or scheduled
alert delivery yet. Sparse snapshots cannot enforce a maximum loss. Users must
not supply a fabricated source timestamp or mark unknown flow history verified
just to obtain a below_threshold result.
