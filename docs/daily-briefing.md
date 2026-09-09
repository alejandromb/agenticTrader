# Daily briefing workflow

When the user asks for a daily briefing, collect authorized read-only account
data, reconcile available fills/funding, review relevant primary-source news and
events, then update the private local file `data/briefings/latest.json` (relative
to the configured database's parent directory). Validate against Briefing in
`src/agentic_trading/briefing.py`. Preserve earlier editions in dated private
files before replacing them; never commit actual account data.

Start the existing loopback dashboard if needed, then open `/briefing` in the
embedded browser. Current preview is `http://127.0.0.1:8766/briefing`:

```sh
.venv/bin/agentic-trading dashboard --port 8766
```

The page rereads local content for every request and uses no-store headers.
Refreshing does not fetch broker data/news. Missing content shows an empty state;
invalid content returns a generic error without leaking private data. Prior-day
briefings show an older-snapshot warning. Dates in the page header use UTC;
source retrieval details should also include the user's local time.

Keep the first screen concise: account status, decision summary, material events,
work queue. Put detailed uncertainties in the limitations disclosure, while
material freshness/funding gaps remain visible on summary cards. The UI follows
readability guidance: responsive layout, readable type and source links, no
decorative charts. No external fonts, analytics, hosting or model calls.

After reading, the user discusses decisions and assigns work in chat. There are
no trade buttons, scheduled jobs, automatic refreshes, or approvals on this page.
Only the renderer/assets are versioned; briefing data is private and Git-ignored.
Known limitation: not an archived-edition browser or live connector yet. The
local server must be running for the page to open; this is not an always-on bot.
