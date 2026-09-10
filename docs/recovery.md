# Recovery and backup boundaries

Code is committed and pushed to the private repository
https://github.com/alejandromb/agenticTrader under the user's personal account.
The local main branch tracks origin/main. GitHub code backup does not include
private runtime data. User explicitly selected this owner and repository name.

Private data is not protected by Git: database, artifacts and briefing/review
files are ignored. A consistent SQLite backup was made using its backup API
under data/backups on September 10 and passed PRAGMA integrity_check. This is
a database-only local recovery copy, not a full backup, off-device protection,
or proof of a complete application restore. Do not copy a live SQLite file with
ordinary file copying and assume consistency.

Next: choose an encrypted off-device destination; include database plus referenced
artifact files, review/briefing history and manifests. Exclude .env/API credentials
from code and ordinary backup bundles; manage secrets separately. Test restoration
in an isolated directory, validate SQLite integrity and each referenced SHA-256,
then exercise saved-run and candidate-history reads before declaring recovery
ready. Do not overwrite the live database during a restore test.
