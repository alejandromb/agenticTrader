# Agentic Trading

Agentic Trading is an evidence-driven investment research copilot. It captures
public filings, extracts traceable financial facts, produces structured AI
analysis, and preserves every artifact for review.

It is advisory software. It does not place trades, allocate capital, or replace
human investment judgment.

## Version 1 capability

Version one can:

- resolve a U.S. public company from its ticker;
- capture its latest Form 10-K or explicitly selected Form 10-Q from SEC EDGAR;
- store the filing as a content-addressed artifact;
- extract annual or period-safe quarterly financial facts without mixing filing
  contexts;
- persist source-linked facts, filing statements, and deterministic calculation
  claims;
- calculate revenue growth, operating margin, net margin, free-cash-flow
  approximation, and current ratio with formula and input-claim lineage;
- explain cash allocation across capital expenditure, acquisitions, dividends,
  repurchases, and debt activity when disclosed;
- extract management's capex rationale and quantified allocation-table details;
- detect and visibly retain cross-filing value revisions without automatically
  calling them restatements;
- generate strict OpenAI analysis covering strengths, concerns, trends, cash
  allocation, uncertainties, and known limitations;
- force every persisted evidence gap into the known-limitations output; and
- retain runs, sources, transitions, claims, calculations, audits, model/prompt
  metadata, responses, and analysis lineage in SQLite.

Version one is complete when one company can be researched and later reviewed
with its filing, facts, calculations, revision audits, limitations, and analysis
lineage intact. It intentionally excludes valuation, portfolio construction,
broker integration, order intent, and execution.

## Quick start

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
cp .env.example .env
```

Configure `OPENAI_API_KEY` and `SEC_USER_AGENT` in `.env`, then verify setup:

```bash
.venv/bin/agentic-trading doctor
```

Start the local dashboard:

```bash
.venv/bin/agentic-trading dashboard
```

Then open `http://127.0.0.1:8765`. This is the recommended interface for
starting company research, reading saved memos, reviewing limitations, and
recording the human disposition. Press `Ctrl+C` in the terminal to stop it.
The same dashboard includes the quantitative lab, decision monitoring, alert
ledger, and research-refresh reviews. Research and Reviews are primary;
Quant lab and Monitoring remain available under Tools so advanced forms do not
compete with the main decision workflow.

Run company research:

```bash
.venv/bin/agentic-trading research-company AAPL \
  --question "Assess the company's financial condition and identify the next research needed."
```

Annual 10-K research is the default. For a bounded quarterly update, add
`--form 10-Q`; quarterly values are not annualized and do not generate DCF
scenarios.

The command creates `data/agentic-trading.db` and stores source artifacts under
`artifacts/`. Both paths are excluded from Git.

See [docs/user-guide.md](docs/user-guide.md) for the workflow and
[docs/development.md](docs/development.md) for engineering setup. Dashboard
operation and boundaries are documented in [docs/dashboard.md](docs/dashboard.md).

## Safety boundary

AI output is untrusted analysis. Every analytical point must reference captured
claims, humans retain final authority, and no broker integration exists in
version one. The governing decisions are in `docs/decisions/`.

## Review a saved run

```bash
.venv/bin/agentic-trading list-runs
.venv/bin/agentic-trading show-run YOUR_RUN_ID
```

The detailed view shows evidence claims, calculation formulas and input IDs,
cross-filing revision audits, structured analysis, and known limitations.

## Version 2 capability

Version two extends the accepted financial pipeline into a complete research
decision record. It adds:

- bounded, source-linked Item 1 business and Item 1A risk evidence;
- business-quality and material-risk analysis;
- explicit bull, base, bear, and devil's-advocate cases;
- deterministic bear/base/bull DCF sensitivities with formula, assumption, and
  input-claim lineage;
- a validated, immutable schema-2.0 investment memo;
- persisted model token usage and latency; and
- a separate, append-only human disposition command.

See [docs/version-2.md](docs/version-2.md) and
[docs/evaluation/version-two-acceptance.md](docs/evaluation/version-two-acceptance.md).

Portfolio analytics, backtesting, automation, and broker execution remain out
of Version 2 scope.

Record a decision only after reviewing the memo:

```bash
.venv/bin/agentic-trading record-disposition YOUR_RUN_ID watch \
  --rationale "Wait for stronger evidence"
```

## Milestone 3 quantitative lab

Milestone 3 provides a point-in-time quantitative lab for deterministic research
screens, hypothetical portfolio analytics, risk metrics, and cost-aware
backtesting. It remains disconnected from brokers and cannot place or propose
orders. All inputs, parameters, strategy versions, and results are persisted for
reconstruction. See [docs/milestone-3.md](docs/milestone-3.md) and the
[acceptance audit](docs/evaluation/milestone-three-acceptance.md).

## Milestone 4 decision monitoring

Milestone 4 turns eligible human-reviewed decisions into explicit local watch
criteria. Humans define price or drawdown thresholds; evaluations retain the
immutable dataset hash and `as_of` boundary; repeated evaluations cannot create
duplicate alerts; and acknowledgement is a separate human event. Monitoring is
manual and has no live feed, scheduler, notification delivery, model call, or
execution path. See [docs/milestone-4.md](docs/milestone-4.md) and the
[acceptance audit](docs/evaluation/milestone-four-acceptance.md).

## Milestone 5 research-refresh reviews

Milestone 5 compares two completed same-company research records without asking
a model to judge the change. The persisted packet separates exact-period claim
changes from cross-period metric movement, identifies limitation and section
changes, links time-bounded baseline-monitor alerts, and awaits one explicit
human outcome. It cannot refresh research automatically or mutate a memo,
monitor, portfolio, or broker. See [docs/milestone-5.md](docs/milestone-5.md) and
the [acceptance audit](docs/evaluation/milestone-five-acceptance.md).

## Milestone 9 research-quality ledger

Milestone 9 evaluates saved research artifacts using five reproducible integrity
gates and six human-scored criteria. Results retain prompt, model, schema, token,
and latency context in an append-only ledger. The score evaluates research
quality—not the company, later stock returns, or investment attractiveness—and
does not call a model. See [docs/milestone-9.md](docs/milestone-9.md).

## Milestone 10 automatic market data

The Quant workflow is designed around a read-only market-data provider boundary:
explicitly requested daily adjusted stock bars are normalized and immediately
persisted through the existing immutable price-dataset contract. Alpaca is
implemented as an optional adapter, but paid market data is not a v1 dependency.
When no low-cost provider is configured, explicit CSV import remains the
auditable fallback. The adapter uses historical market data only and contains no
account, position, order, or trading client. See
[docs/milestone-10.md](docs/milestone-10.md).
