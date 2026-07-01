# User Guide

## What the platform does

The current platform researches one U.S. public company at a time from its
latest annual SEC filing. A successful run moves through:

```text
ticker -> SEC filing -> stored evidence -> financial claims
       -> structured OpenAI analysis -> challenge-ready run
```

The output is a research artifact, not a buy or sell instruction.

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

This command:

1. migrates the local database;
2. resolves the ticker with the SEC;
3. creates an auditable research run;
4. downloads and hashes the latest Form 10-K;
5. records source provenance;
6. extracts and persists supported financial claims;
7. sends only those claims and the question to OpenAI;
8. validates every returned claim reference;
9. persists the structured analysis; and
10. leaves the run in `challenging` for the next workflow stage.

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
- `analysis`: assessment, summary, strengths, concerns, and uncertainties.

Every point inside the analysis contains `claim_ids`. These link back to the
financial facts used for that statement.

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

## Current limitations

- Only annual Form 10-K research is orchestrated.
- The minimum snapshot currently includes revenue, net income, assets,
  liabilities, and operating cash flow.
- No valuation, price, portfolio, or brokerage workflow is included.
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
