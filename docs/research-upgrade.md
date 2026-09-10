# Research operating system upgrade

This is a staged engineering effort, not certification as an institutional fund.
Long-term research, human authority, no new leverage or execution automation.

## Work packages and acceptance gates

| Package | Outcome | Acceptance evidence | State |
| --- | --- | --- | --- |
| Discovery integrity | Broker scans plus market-wide earnings events | Raw inputs retained; duplicates/conflicts/quarantine explicit | Calendar implemented; original scanner returned zero |
| Universe expansion | Repeatable liquid-stock quality, value and catalyst lanes | Versioned filters, returned/total counts, explicit truncation and unknowns | Liquid-stock scanner created; 399 matches, 200 returned; other lanes pending |
| Research funnel | Discovered → verified → valuation → human review, or deferred/rejected | Source-linked reason at every stage; no omitted losers | Durable research-stage ledger and live history implemented; verification/approval gates pending |
| Valuation discipline | Normalized cash flow, bear/base/bull assumptions and sensitivity | Reproducible arithmetic; filing revisions and valuation basis visible | Pending |
| Portfolio fit | Incremental concentration and downside before allocation | Fresh verified account context, funding and proposed exposure | Existing snapshot foundation; integration pending |
| Experiment ledger | Frozen paper picks and deferrals versus SPY | Same dates, adjusted data, cost assumptions, no look-ahead | Prospective pilot frozen; arithmetic helper tested; price ingestion and results pending |
| Operator workflow | Briefing shows health, coverage, shortlist and blocked gates | User can distinguish data outage from no opportunities | Database history, hash checks and coverage implemented; no live broker refresh |

## Discovery policy v1

Use Robinhood for discovery, SEC/issuer documents for verifying facts, and our
existing research persistence for full analyses. Do not duplicate brokerage
execution. Tool availability in this chat does not establish an authenticated
background transport in the Python app.

Market-wide earnings is a discovery lane, not the whole investable universe.
Calendar normalizer retains raw rows and source indices. Exact duplicates are
collapsed, conflicting records for a company-quarter quarantined, and events
outside the requested window excluded visibly. Fiscal years more than one year
from the current calendar year require verification, not automatic rejection of
the business. Broker-confirmed dates are not independently issuer-verified.
Do not infer listing eligibility, liquidity or quality from the calendar filter.

Saved scanner reads must retain total match count, returned rows, sorting and
filters if returned. Zero results does not establish no market opportunities.
Do not relabel a failed or empty scanner as a successful broad valuation screen.
Existing user scanner configurations remain untouched unless changes are scoped.

The new liquid-stock scanner uses verified filter specs: STOCK asset type,
market cap >= $2B, 30-day daily average share volume >= 500,000. These are triage
defaults, not strategy parameters validated for alpha. Quality lane can require
positive operating margin; a catalyst lane must not discard unprofitable
companies silently. Never use today's partial volume to compare full sessions.
Percentage filters use decimal ratios, not whole percentages.

## Implementation and replay

Prepare a private JSON object with `provider`, timezone-aware `retrieved_at`,
`start_date`, `days` (1–31 forward), `calendar_rows`, and optional raw scanner
response. Archive and normalize without any remote calls:

```sh
.venv/bin/python -m agentic_trading.discovery data/reviews/discovery-input.json
```

The command returns a SHA-256 ID under data/discovery. Raw input and normalized
output are stored together in the existing immutable artifact store. Replaying
identical input and policy yields identical identity; use LocalArtifactStore.get
to verify integrity. This is not a new database or automated feed.

## Evaluation policy before money

Pre-register a candidate cohort before returns occur: snapshot ID, selection
rule, entry date (next regular session close), evaluation horizons (30 and 90
calendar days, next trading close), equal weighting, SPY benchmark, adjusted
price provider, assumed round-trip costs and missing/delisted treatment. Keep
rejected names as a comparison cohort, with no retrospective replacements.
Require complete entry/exit coverage before aggregate return claims. Separately
score source corrections, thesis failures, research time and cost. Do not tune
filters on the same cohort used to claim success. Small samples are descriptive,
not statistical evidence of an investable edge. Implementation remains pending.
