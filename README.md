# Agentic Trading

An evidence-driven investment research copilot for U.S. equities. Research a
company, inspect the supporting filings and calculations, record your decision,
and return later without losing the evidence or reasoning.

**Research and decision support—not an autonomous trading system.** The app does
not submit orders. AI analysis and valuation scenarios are not guarantees of
accuracy or returns; the investor retains authority.

## What works today

- Company research from SEC 10-K/10-Q filings with structured OpenAI analysis.
- Saved memos, claim-level evidence, calculation lineage, visible filing revisions,
  known limitations and human decision records.
- A local dashboard, quantitative lab and manually evaluated monitoring.
- Deterministic screens, hypothetical portfolio analysis and backtests using
  explicitly supplied, persisted price datasets.
- Private daily briefings and an append-only opportunity research history.

See [Project state](PROJECT_STATE.md) for implemented versus pending work.
There is no verified investment edge, continuous scanner, automatic broker
synchronization or always-on trading bot.

## Quick start

Requirements: Git, Python 3.12 or newer, and access to this private repository.
These commands use a macOS/Linux shell. Start from a reviewed checkout:

```sh
git clone https://github.com/alejandromb/agenticTrader.git
cd agenticTrader
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade 'pip>=26.2.1'
.venv/bin/python -m pip install -e '.[dev]'
test -e .env || cp .env.example .env
chmod 600 .env
```

Edit your local `.env`:

- `SEC_USER_AGENT`: application identification with your real contact address.
- `OPENAI_API_KEY`: your own key, required for generated company analysis.
- `OPENAI_MODEL`: keep the example default or choose a model your account can use.
- Alpaca credentials are optional for the read-only market-data adapter;
  provider entitlements are separate. Paid market data is not required to start.

Never paste keys into commits, issues or screenshots. Live research makes SEC
and model-provider requests and can incur API charges. Viewing saved data does
not require a fresh model call.

```sh
.venv/bin/agentic-trading doctor
.venv/bin/agentic-trading dashboard --port 8766
```

Open [the dashboard](http://127.0.0.1:8766/) or
[the daily briefing](http://127.0.0.1:8766/briefing).
Keep the terminal running; press Ctrl+C to stop. Without `--port`, the default
is 8765. If the address is already in use, check the existing server or choose
another port; do not terminate an unfamiliar process.

Keep the dashboard loopback-only. Do not expose it to your LAN or the internet.

## Daily workflow

1. Open the briefing and check timestamps, funding uncertainty and limitations.
2. Inspect company research and supporting evidence.
3. Record a human disposition after reviewing the memo; it is not a broker order.
4. Use Tools for quantitative analysis or manual monitoring when suitable price
   data is available. Company filings alone do not supply price history.

**Refreshing the briefing does not fetch new holdings, prices or news.** It reads
the locally prepared briefing and saved opportunity ledger. A new installation
has no personal briefing until one is prepared. Chat-connected Robinhood tools
are separate from this application; cloning the repository does not connect an
account.

See the [user guide](docs/user-guide.md), [dashboard guide](docs/dashboard.md)
and [briefing preparation workflow](docs/daily-briefing.md).

### CLI examples

```sh
.venv/bin/agentic-trading research-company AAPL \
  --question "Assess financial condition, cash allocation and evidence gaps."
.venv/bin/agentic-trading list-runs
.venv/bin/agentic-trading show-run YOUR_RUN_ID
.venv/bin/agentic-trading record-disposition YOUR_RUN_ID watch \
  --rationale "Wait for stronger evidence"
.venv/bin/agentic-trading --help
```

Annual 10-K research is the default. Add `--form 10-Q` for a bounded quarterly
update; quarterly values are not annualized into DCF scenarios.

## Private data and source of truth

Each installation owns its credentials and data. Collaborators share software,
not a portfolio or brokerage connection.

| Location | Purpose | In Git? |
| --- | --- | --- |
| Source, tests, migrations, docs | Reviewed software and synthetic examples | Yes |
| `.env` | Installation-specific credentials and configuration | No |
| `data/` | Database, private briefings, snapshots and reviews | No |
| `artifacts/` | Captured evidence and immutable research artifacts | No |
| Robinhood | Authoritative broker holdings, cash, orders and fills | No |

Local broker snapshots are dated observations, not live balances. Research and
decisions belong to the local research record. The default database is
`data/agentic-trading.db`; evidence is stored under `artifacts/`.

GitHub backs up code, **not private research data**.
See [recovery boundaries](docs/recovery.md) for backup gaps and restore requirements.

## Optional Docker CLI

Docker is optional. Use the local setup above for the browser dashboard;
Compose currently publishes no web port.

```sh
docker compose build app
docker compose run --rm app init-db /app/data/agentic-trading.db
docker compose run --rm app --help
docker compose --profile test run --rm --build test
```

The application container runs non-root with a read-only root filesystem,
dropped capabilities and no privilege escalation. Named volumes persist
`/app/data` and `/app/artifacts` across container recreation. They are separate
from your host checkout's directories: existing local data is not automatically
migrated into Docker.

**Do not run `docker compose down -v` unless you intend to delete the volumes.**
Volumes are not encrypted backups. Do not run concurrent app replicas against
the same SQLite file. Compose supplies explicitly listed credentials at runtime,
not in the image; host/Docker administrators can still inspect them.

## Development and safe collaboration

Read [SECURITY.md](SECURITY.md) before using private data or keys. Review incoming
code, dependencies, migrations and build scripts before executing them. Test
collaborator changes with synthetic data and no credentials.

```sh
.venv/bin/pytest
.venv/bin/ruff check .
.venv/bin/ruff format --check .
git diff --check
```

Use a branch and pull request: `main` requires an approving review.
GitHub Actions is currently disabled; local tests are not an enforced CI gate.
Run the redacted secret checks in SECURITY.md before pushing. Never commit real
portfolios or database exports—even to this private repository.

## Architecture and roadmap

Python CLI and loopback web server, SQLAlchemy ORM with Alembic migrations,
SQLite workflow state, content-addressed evidence and structured model outputs.
Deterministic calculations remain separate from generated commentary.

- [Current progress and priorities](PROJECT_STATE.md)
- [Architecture decisions](docs/decisions/README.md) and [session handoffs](docs/sessions/README.md)
- [Engineering setup](docs/development.md) and [version-two research contract](docs/version-2.md)
- [Research upgrade plan](docs/research-upgrade.md), [opportunity radar](docs/opportunity-radar.md), [decision ledger](docs/opportunity-ledger.md)
- [Prospective paper evaluation](docs/paper-evaluation.md) and [portfolio context](docs/milestone-11.md)

Crypto/scalping and live execution are not current product capabilities.
Experimental execution projects remain separate until explicitly reviewed safety
and product contracts exist. Add features because they improve decision quality,
not simply because they add more data or charts.
