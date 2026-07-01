# Local Dashboard v1 Acceptance Audit

- Date: 2026-07-01
- Result: Accepted
- Surface: Loopback-only research dashboard

## Contract audit

| Requirement | Evidence | Result |
| --- | --- | --- |
| Explicit startup | Dashboard starts only through the `dashboard` CLI command | Pass |
| Loopback only | Address validation rejects `0.0.0.0`; server binds validated loopback without reverse DNS | Pass |
| Secret safety | API exposes configuration booleans and never returns key or user-agent values | Pass |
| Request protection | State-changing JSON requests require an unguessable process token in a custom header | Pass |
| Input bounds | Content type, body size, JSON object shape, ticker, question, status, and rationale are validated | Pass |
| Existing services | Research uses `CompanyResearchService`; disposition uses existing repositories and workflow transition | Pass |
| Saved reconstruction | Run list/detail recover memo, analysis, limitations, telemetry, audits, and disposition eligibility | Pass |
| Human authority | Decision form is shown only while awaiting disposition and warns that no trade is placed | Pass |
| Browser behavior | Real database rendered 11 runs, configuration readiness, a complete WMT memo, and the research form | Pass |
| Responsive layout | Desktop and 390px browser checks completed with document width equal to viewport width | Pass |
| External isolation | CSP allows only same-origin scripts/styles/connections; no external asset is loaded | Pass |
| Regression safety | 110 automated tests, lint, formatting, and whitespace checks pass | Pass |

## Known limitations

- The dashboard is a single-user local tool, not an authenticated remote service.
- The request token protects browser-originated writes but is not a defense
  against malicious software already running as the same local user.
- Company research is synchronous; the page waits while SEC acquisition and the
  paid OpenAI request complete.
- Restarting the server invalidates open-page request tokens; reload the page.
- The first dashboard release covers research, saved-run review, and human
  disposition. Quantitative, monitoring, and refresh-review workflows remain in
  the CLI.
- Disposition persistence and workflow completion use the existing two-step
  service behavior; a process crash between those operations would require
  recovery tooling.

## Browser verification boundaries

The real saved-run and form surfaces were exercised read-only. No paid research
request was submitted and no human disposition was selected on the user's live
database during acceptance.
