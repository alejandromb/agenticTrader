# Agentic Trading

Agentic Trading is an evidence-driven investment research copilot. It captures
public filings, extracts traceable financial facts, produces structured AI
analysis, and preserves every artifact for review.

It is advisory software. It does not place trades, allocate capital, or replace
human investment judgment.

## Version 1 capability

Version one can:

- resolve a U.S. public company from its ticker;
- capture its latest Form 10-K from SEC EDGAR;
- store the filing as a content-addressed artifact;
- extract current and comparable annual financial facts without mixing filing
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

Run company research:

```bash
.venv/bin/agentic-trading research-company AAPL \
  --question "Assess the company's financial condition and identify the next research needed."
```

The command creates `data/agentic-trading.db` and stores source artifacts under
`artifacts/`. Both paths are excluded from Git.

See [docs/user-guide.md](docs/user-guide.md) for the workflow and
[docs/development.md](docs/development.md) for engineering setup.

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

## Version 2 roadmap

Version two is the complete research decision record: source-linked business and
risk analysis, deterministic valuation scenarios, bull/base/bear cases,
devil's-advocate challenge, a canonical investment memo, and a separately
recorded human disposition. See [docs/version-2.md](docs/version-2.md).

Portfolio analytics, backtesting, automation, and broker execution remain out
of scope.
