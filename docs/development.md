# Development

## Local Python environment

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
```

## Docker

Build the runtime image:

```bash
docker compose build app
```

Run the test image:

```bash
docker compose --profile test run --rm test
```

Initialize the persistent workflow database:

```bash
docker compose run --rm app init-db /app/data/agentic-trading.db
```

Validate the example memo by mounting repository examples read-only:

```bash
docker compose run --rm \
  -v ./examples:/app/examples:ro \
  app validate-memo examples/investment-memos/aapl-2025-example.json
```

## SEC identification

Copy `.env.example` to `.env` and replace its placeholder with a real contact
before performing live SEC requests. Compose passes `SEC_USER_AGENT` at runtime;
it is not stored in the image. `.env` is excluded from Git.

For live model evaluation, set `OPENAI_API_KEY` in the same local `.env`. The
default model is the pinned `gpt-5.4-2026-03-05` snapshot and can be overridden
with `OPENAI_MODEL` for explicit experiments. Neither value is persisted in the
database; each generated artifact will record the model actually used.

## Persistence boundary

The Compose volumes retain the SQLite database and captured artifacts across
container replacement. Version one is intentionally single-process. Do not run
multiple application replicas against the same SQLite file.
