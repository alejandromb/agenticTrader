# User Guide

## What the platform does

The Version 2 platform researches one U.S. public company at a time from its
latest explicitly selected annual or quarterly SEC filing. A successful
research run moves through:

```text
ticker -> SEC filing -> stored evidence -> financial claims
       -> calculations + business/risk evidence + valuation scenarios
       -> structured analysis -> validated memo
       -> awaiting human disposition
```

The output is a research artifact, not a buy or sell instruction.

## Recommended interface

Start the local dashboard:

```bash
.venv/bin/agentic-trading dashboard
```

Open `http://127.0.0.1:8765`. From there you can:

1. enter a ticker and research question;
2. wait for the SEC and OpenAI workflow to finish;
3. open saved research from the left-hand ledger;
4. read the thesis, counter-thesis, limitations, cases, risks, valuation, and
   model telemetry; and
5. record your human disposition when the run is ready.

The top navigation keeps `Research` and `Reviews` visible. Open `Tools` to reach:

- `Quant lab` for immutable price import, screens, holdings analytics, and
  backtests;
- `Monitoring` for explicit watch rules, point-in-time evaluation, alerts, and
  acknowledgement; and
- `Reviews` for comparing completed same-company research and recording a human
  refresh outcome.

Advanced tools are collapsed under the investment question they answer. Click
the question card to open its form. When a workflow has no eligible inputs, the
dashboard displays the missing prerequisite and a button for the next step. For
example, Monitoring requires a completed `watch` or `consider_for_portfolio`
human disposition, and price-based workflows require an imported immutable
price dataset.

The terminal must remain open while using the dashboard. Press `Ctrl+C` to stop
the server. It accepts loopback connections only and is not a remote web app.
The CLI sections below remain useful for reproducible diagnostics and scripted
workflows, but the accepted capabilities no longer require terminal commands.

## First-time setup

Create the Python environment and install the application:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
cp .env.example .env
```

Edit `.env` locally:

```dotenv
SEC_USER_AGENT=AgenticTrading/0.1 your-contact@example.com
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-5.4-2026-03-05
```

Never commit `.env` or paste its key into chat, logs, or documentation.

## Check configuration

```bash
.venv/bin/agentic-trading doctor
```

The command reports only booleans. It never prints secret values.
`database_exists` is expected to be `false` before the first research run.

## Research a company

```bash
.venv/bin/agentic-trading research-company WMT \
  --question "Assess fiscal financial condition, major strengths, concerns, and missing evidence."
```

The default is the latest Form 10-K. To run a quarterly update instead:

```bash
.venv/bin/agentic-trading research-company WMT --form 10-Q \
  --question "Assess the latest quarter and identify what still requires annual evidence."
```

This command:

1. migrates the local database;
2. resolves the ticker with the SEC;
3. creates an auditable research run;
4. downloads and hashes the latest explicitly selected Form 10-K or 10-Q;
5. records source provenance;
6. extracts current and comparable annual facts from one filing context;
7. detects changed values across filing accessions;
8. creates deterministic calculations with formula and input lineage;
9. extracts supported capital-allocation narrative and table details;
10. sends only validated claims, calculations, gaps, and the question to OpenAI;
11. validates every returned claim reference;
12. persists revision audits, known limitations, and structured analysis; and
13. synthesizes and validates a schema-2.0 investment memo;
14. records model input/output tokens and request latency; and
15. leaves the run in `awaiting_human_disposition`.

The command performs external SEC requests and one paid OpenAI request.

## Custom storage paths

```bash
.venv/bin/agentic-trading research-company AAPL \
  --database data/research.db \
  --artifact-root artifacts \
  --question "Assess fiscal financial condition."
```

## Read the output

The command prints JSON containing:

- `run_id`: durable workflow identity;
- `analysis_artifact_id`: persisted analysis identity;
- `filing_accession`: exact SEC filing;
- `model` and `prompt_version`: reproducibility metadata;
- `state`: current workflow checkpoint; and
- `memo_artifact_id`: immutable canonical memo identity;
- `model_usage`: input tokens, output tokens, and request latency; and
- `analysis`: assessment, summary, strengths, concerns, trends, cash allocation,
  uncertainties, and known limitations.

Every analytical point contains `claim_ids`. These link to issuer-reported facts,
filing statements, or deterministic calculation claims. Calculation statements
include their formulas and input claim IDs.

## Review saved research

List all runs:

```bash
.venv/bin/agentic-trading list-runs
```

Display one run in a human-readable form:

```bash
.venv/bin/agentic-trading show-run YOUR_RUN_ID
```

The run ID is printed by `research-company` and appears in `list-runs`.
The detailed view also displays the cross-filing revision-audit count and both
accession/value pairs for every detected revision.

## Record the human disposition

After reviewing the saved run and memo:

```bash
.venv/bin/agentic-trading record-disposition YOUR_RUN_ID watch \
  --rationale "Wait for another filing and stronger valuation evidence"
```

Allowed dispositions are `investigate`, `watch`, `reject`, and
`consider_for_portfolio`. This explicit command creates an append-only human
event and moves the run to `complete`. It does not modify the memo. The model
cannot invoke this command or choose the human disposition.

## Current limitations

- Annual Form 10-K and quarterly Form 10-Q research are orchestrated explicitly;
  annual remains the default.
- Analysis is limited to facts and narrative supported by the selected filing
  and SEC company-facts data. Quarterly research does not refresh complete
  annual business/risk evidence, annualize values, or generate DCF scenarios.
- Cross-filing value differences are labeled neutrally; a formal restatement
  label requires explicit filing evidence.
- Capital-allocation table extraction is deterministic and issuer layouts can
  still produce an explicit evidence gap.
- Market data is imported manually as immutable adjusted-price CSV snapshots;
  there is no live feed.
- Portfolio analytics are hypothetical and read-only. Backtests support only a
  versioned long/cash moving-average strategy and are not forecasts.
- No command proposes or creates orders, changes holdings, or accesses a broker.
- Valuation is limited to assumption-driven cash-flow sensitivities; it is not
  equity fair value or a price target and lacks market-price comparison.
- SEC concepts can differ across issuers; missing optional metrics are recorded
  as evidence gaps, while unsupported required inputs fail explicitly.
- A command-line interface is the current product surface.

## Useful engineering commands

```bash
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

For lower-level diagnostic commands, run:

```bash
.venv/bin/agentic-trading --help
```

## Milestone 3 quantitative workflows

Open `Tools` → `Quant lab` → “What price history does this investigation need?”
to see the current data path. If a read-only market-data provider is configured,
enter comma-separated tickers and dates and the backend will persist the fetched
daily bars automatically. Alpaca is supported as an optional adapter through
`ALPACA_API_KEY` and `ALPACA_SECRET_KEY`, but paid market-data access is not
required for v1.

The equivalent CLI workflow is:

```bash
.venv/bin/agentic-trading fetch-prices AAPL SPY \
  --start 2025-01-01 --end 2026-01-01 --feed iex
```

For the optional Alpaca adapter, `iex` is the basic feed and `sip` should be
selected only when the account has that paid data entitlement. No broker account,
position, or order API is used.

When no provider is configured, import an explicit adjusted-price CSV. The exact
bytes and SHA-256 are retained:

```bash
.venv/bin/agentic-trading import-prices prices.csv \
  --source "Documented source and retrieval date"
```

Run an as-of screen over persisted research memos:

```bash
.venv/bin/agentic-trading screen-research \
  --as-of 2026-07-01T00:00:00Z \
  --min-revenue-growth 3 \
  --min-free-cash-flow 0
```

Analyze a hypothetical `ticker,shares` holdings file against an aligned
benchmark. The latest common observation not after `as_of` is used:

```bash
.venv/bin/agentic-trading analyze-portfolio holdings.csv \
  --dataset DATASET_ID --benchmark SPY --as-of 2026-06-30
```

Run the versioned moving-average simulation with explicit costs:

```bash
.venv/bin/agentic-trading backtest DATASET_ID \
  --ticker AAPL --benchmark SPY \
  --short-window 20 --long-window 100 \
  --initial-cash 10000 --transaction-cost-bps 10
```

Signals use only history available through their signal date and execute on the
next common observation. Results are analytical artifacts only; they cannot be
sent to DiveTrader, Alpaca, or another execution system.

## Decision monitoring

After a human completes a research run with `watch` or
`consider_for_portfolio`, define explicit criteria in a JSON rules file as
documented in [the Milestone 4 contract](milestone-4.md). Then create and
evaluate the monitor:

```bash
.venv/bin/agentic-trading create-monitor YOUR_RUN_ID \
  --name "Apple follow-up" --rules monitor-rules.json

.venv/bin/agentic-trading evaluate-monitor MONITOR_ID \
  --dataset DATASET_ID --as-of 2026-06-30
```

Review open alerts and record a human acknowledgement:

```bash
.venv/bin/agentic-trading list-alerts --monitor MONITOR_ID --status open

.venv/bin/agentic-trading acknowledge-alert ALERT_ID \
  --note "Reviewed against the current research memo"
```

Evaluation does not fetch prices. Import a new immutable dataset first, then
select it explicitly. An alert is evidence that a human-defined condition was
met; it is not an investment recommendation and cannot trigger another action.

## Research-refresh reviews

After completing newer research for the same ticker, compare it with the prior
completed run:

```bash
.venv/bin/agentic-trading compare-research \
  BASELINE_RUN_ID CURRENT_RUN_ID
```

The JSON packet identifies exact-period claim changes, explicitly labeled
period shifts in latest metrics, added/resolved limitations, changed memo
sections, and baseline-monitor alerts evaluated between the two run boundaries.
It does not decide whether a change is material or favorable.

Retrieve the packet later and record the human review outcome:

```bash
.venv/bin/agentic-trading show-research-review REVIEW_ID

.venv/bin/agentic-trading record-review-outcome REVIEW_ID investigate \
  --rationale "The new debt evidence requires follow-up"
```

Allowed outcomes are `no_thesis_change`, `revise_thesis`, `investigate`, and
`close_watch`. These are append-only review records. Even `close_watch` does not
change a monitor or trigger another workflow.

## Research-quality evaluations

Create a JSON score file containing exactly the six rubric criteria. Every
criterion requires a score from 0 to 2 and a human rationale:

```json
{
  "numerical_fidelity": {"score": 2, "rationale": "Values and periods match the cited claims."},
  "evidence_fidelity": {"score": 2, "rationale": "Conclusions stay within cited evidence."},
  "fact_judgment_separation": {"score": 2, "rationale": "Judgments are labeled as analysis."},
  "balance": {"score": 2, "rationale": "Credible strengths and concerns are present."},
  "uncertainty": {"score": 2, "rationale": "Material evidence gaps remain visible."},
  "decision_usefulness": {"score": 2, "rationale": "The memo identifies useful follow-up work."}
}
```

Record and retrieve evaluations:

```bash
.venv/bin/agentic-trading evaluate-research-quality RUN_ID \
  --scores quality-scores.json

.venv/bin/agentic-trading list-research-evaluations --run-id RUN_ID
```

Acceptance is derived: all integrity gates must pass, no score may be zero, and
the total must be at least 9 of 12. This does not score later returns, judge the
company, or change the run's human disposition.
