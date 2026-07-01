# Agentic Trading

Agentic Trading is an evidence-driven investment research copilot. It captures
public filings, extracts traceable financial facts, produces structured AI
analysis, and preserves every artifact for review.

It is advisory software. It does not place trades, allocate capital, or replace
human investment judgment.

## Current capability

Version one can:

- resolve a U.S. public company from its ticker;
- capture its latest Form 10-K from SEC EDGAR;
- store the filing as a content-addressed artifact;
- extract a minimum annual financial snapshot;
- persist evidence-linked claims;
- generate strict OpenAI financial analysis; and
- retain run, model, prompt, response, and claim lineage in SQLite.

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
