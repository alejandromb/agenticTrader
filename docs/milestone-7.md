# Milestone 7 Product Contract

## Outcome

Add trustworthy quarterly research updates without confusing discrete-quarter,
year-to-date, instant, or annual accounting periods.

## User workflows

```text
research-company TICKER --form 10-Q --question QUESTION
```

The dashboard research form exposes `Annual 10-K` and `Quarterly 10-Q`. Annual
remains the default.

## Period contract

| Metric family | Quarterly context |
| --- | --- |
| Revenue, net income, operating income | Shortest valid 60–120 day context ending on report date |
| Operating/investing/financing cash flow, capex, acquisitions, dividends, repurchases, debt flows, net cash change | Longest valid 60–300 day context ending on report date |
| Assets, liabilities, cash, current accounts, debt balances | Instant at report date |

Calculations pair facts only when their start and end dates are compatible.
Revenue growth compares like-duration quarters presented in the same accession.
Margins use discrete-quarter numerator and denominator. Free cash flow uses
year-to-date operating cash flow and capex. Current ratio uses same-date instant
facts.

## Output boundaries

- Claims state whether a duration is discrete-quarter or year-to-date.
- No quarterly value is annualized.
- No DCF scenario is generated from quarterly/YTD cash flow.
- Missing full annual business/risk evidence is visible in known limitations.
- Output remains research, not guidance, forecast, recommendation, or execution.

## Acceptance

Accepted on 2026-07-01 with 118 passing tests and a read-only live Apple 10-Q
extraction smoke test. See `docs/experiments/0006-quarterly-period-integrity.md`.
