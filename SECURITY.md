# Security and private installations

This repository contains shared software, not a shared brokerage account.
Robinhood remains authoritative for balances, holdings, orders and fills.
Local snapshots must retain their source timestamps and are not live balances.

## Credentials and private data

- Never commit credentials, real portfolios, account identifiers, database dumps,
  or private briefing/research artifacts. Use synthetic test fixtures.
- Each installation supplies its own credentials outside Git and Docker images.
  Prefer restricted, read-only credentials where supported; do not share tokens.
- `.env`, `data/`, `artifacts/`, databases and key files are excluded from Git.
  Docker build context also excludes secrets and local runtime data.
- Compose persists database and evidence in separate named volumes. Recreating
  containers preserves them; `docker compose down -v` deletes volumes. Volumes
  are not encrypted backups and do not protect data from the host administrator.
- Compose injects explicitly listed environment variables. Host/Docker
  administrators can inspect them. Never publish `docker compose config` output
  without `--quiet`, environment dumps, logs or diagnostic bundles containing keys.
- Do not mount personal data or supply keys when testing collaborator changes.
  Use a separate checkout/container with synthetic data, no Docker socket, no
  host home-directory mount and no broker connection. Container isolation is
  not a guarantee against malicious code.

## Collaboration and review

Main requires one approving review, stale approvals are dismissed, administrator
bypass is disabled, and force pushes/deletions are blocked. GitHub Actions is
disabled for now; enabling CI, especially self-hosted runners, needs explicit
security review. Dependency alerts are enabled. Hosted secret scanning was not
available for this private repository when checked on 2026-09-10.

Review source, dependency changes, Docker/build scripts, migrations and agent
instructions before executing incoming code. Git hooks and tests themselves
are executable code. No automatic pull-and-run workflow is permitted. A review
requirement does not prove safety; repository administrators can change settings.

Before pushing, use an independently installed Gitleaks (never paste findings):

```sh
gitleaks git . --log-opts=--all --redact=100 --ignore-gitleaks-allow
gitleaks git . --pre-commit --staged --redact=100 --ignore-gitleaks-allow
git diff --cached --check
```

These are local checks, not server-enforced push protection; pattern scanners
can miss credentials and personal financial information. Inspect staged paths
and diff as well. No scan establishes that every possible secret is absent.

## Local dashboard

Keep the dashboard loopback-only. Host and Origin validation rejects DNS
rebinding/cross-origin requests; mutations also require the per-process CSRF
token. This is not multi-user authentication. Do not expose it through a public
tunnel, LAN bind or reverse proxy. Docker Compose deliberately publishes no port.

## Suspected exposure

Stop execution and privately notify the repository owner; never paste secrets
into GitHub issues. Revoke/rotate exposed credentials at the provider, check
provider activity and broker orders, then remediate affected files and history.
Deleting a file or making a repo private does not revoke a copied secret.
History rewriting and credential rotation require coordinated owner approval.

The 2026-09-10 installed Python dependency audit reported no known vulnerabilities
after upgrading pip and pytest; the local application itself is not covered by
that advisory scan. Repeat audits regularly and after dependency changes.

Remaining work: independent security review, reproducible dependency locking,
container OS vulnerability scanning, off-device encrypted private-data backups
and restore testing. No live trading
or unattended execution is authorized by installing this software.
