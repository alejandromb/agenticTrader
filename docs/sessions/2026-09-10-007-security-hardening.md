# Session: collaborator security and installation boundaries

User authorized security/key checks and safeguards. No credentials printed,
rotated or shared; no brokerage actions. Existing user changes were absent.

## Applied and verified

- Private GitHub repository retained. Main now requires one review, dismisses
  stale approvals, applies to administrators, requires resolved conversations
  and linear history, and prohibits force pushes/deletions.
- Disabled previously unused Actions and enabled dependency vulnerability alerts.
  No webhook was configured. Hosted secret scanning/push protection request was
  rejected as unavailable; do not claim those are enabled.
- Gitleaks scanned 72 commits across reachable refs with full redaction and no
  inline suppression. Three generic-rule findings were reviewed: ordinary prose
  and test function/argument text, not credentials. No broad allowlist added.
- Compared the one configured local secret value against all reachable Git blobs:
  zero matches. Does not cover unknown/revoked secrets, external clones or logs.
- Restricted .env to 0600 and data/artifacts parent directories to 0700. This does
  not encrypt data or remove previously granted ACLs or external copies.
- Excluded env/key/database and agent metadata from Docker build context; expanded
  Git key-file exclusions. Runtime Compose is read-only, drops capabilities,
  denies privilege escalation, and has bounded temporary storage. Existing named
  volumes and no published ports preserved; no production data migrated.
- Added strict Host/Origin checks before reads and mutations, retaining CSRF
  protection and loopback binding. Nine new HTTP tests; 241 total pass.
- Dependency audit found advisories in pip 25.0 and pytest 8.4.2. Updated local
  pip to 26.2.1 and pytest to 9.1.1; set patched minimum pytest requirement and
  runtime Docker pip floor. Repeat audit found no known vulnerabilities in
  installed dependencies; own application skipped by advisory database.

## Packaging issue found during Docker verification

Initial container database initialization failed because source-relative migration
paths do not work in an installed wheel. Bundle migrations, Alembic configuration
and schemas with wheel and prefer bundled resources. Docker builder now includes
those inputs. No fallback to arbitrary working-directory migration scripts.
Final Docker build passed. An isolated no-network, no-credential container ran
as non-root with read-only root filesystem, validated bundled schema, migrated
a new database, then a second container verified its persistence and SQLite
integrity. Only the named smoke-test volume was removed; personal volumes were
untouched. Compose configuration validates without displaying resolved secrets.

## Limits / handoff

Security is layered, not guaranteed. No CI status check or server-side secret
gate exists. Collaborators can still propose malicious code; review before
execution with private data. No unattended pull/run. Repository administrators
can change protections. Encrypted off-device backups, independent review,
reproducible dependencies and container OS scanning remain open.
Changes use a branch and pull request, not bypassing the new main protections.
Existing dashboard process needs restart to load request-validation changes.
