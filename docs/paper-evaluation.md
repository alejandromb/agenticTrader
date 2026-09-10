# Prospective paper evaluation

`paper_cohort.py` validates and freezes a cohort before entry, then saves the
plan in the content-addressed artifact store. Registration command refuses
retrospective entry and future registration timestamps. A plan records selections,
deferrals, benchmark, horizons, costs, selection rule and missing-data policy.

```sh
.venv/bin/python -m agentic_trading.paper_cohort PRIVATE_PLAN_JSON
```

Initial private pilot is registered for the September 11 regular-session close,
30/90-calendar-day horizons, equal weights, SPY comparison and an assumed 10bp
round-trip cost applied to each group and benchmark. No real positions created.
Dates roll to the first trading close on/after each horizon; entry failure means
incomplete, not a silently changed entry. Actual provider prices are NOT captured
by registration. No scheduler is running; the saved plan is not a broker order.

The arithmetic helper requires every named entry and exit, rejects nonfinite or
invalid values, permits zero only when caller supplies documented total loss,
and does not silently discard missing/delisted names. It does not verify dates
or adjustment basis: a future price-ingestion/evaluation layer MUST verify those
before calling it. No benchmark result or return is currently claimed.

Remaining: automated same-date adjusted-price retrieval, source lineage, audited
delisting treatment, matched benchmark calculation and 30/90-day review display.
Four purposively selected names cannot establish a statistically reliable edge.
