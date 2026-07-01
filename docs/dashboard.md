# Local Dashboard

Start the dashboard from the repository root:

```bash
.venv/bin/agentic-trading dashboard
```

Open `http://127.0.0.1:8765` in a browser. The dashboard reads the same
`data/agentic-trading.db`, `artifacts/`, and `.env` configuration as the CLI.

The first release supports:

- configuration readiness;
- company research using the existing SEC and OpenAI pipeline;
- saved-run browsing;
- readable memo, analysis, limitation, and telemetry views; and
- explicit human disposition for eligible runs.

The server is intentionally local-only. It rejects non-loopback bind addresses,
loads no external assets, and never returns API keys or the SEC user-agent value.
It is not designed for remote hosting or multiple users.

See the [Dashboard v1 acceptance audit](evaluation/dashboard-v1-acceptance.md)
for tested behavior and known limitations.
