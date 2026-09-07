# Session Logs

Session logs preserve concise, append-only handoff history. The canonical
current snapshot lives in the repository-root `PROJECT_STATE.md`.

Create one log for each meaningful work session using:

```text
YYYY-MM-DD-NNN-short-description.md
```

Each log should include:

- objective;
- outcomes;
- decisions made;
- files changed;
- validation performed;
- unresolved questions; and
- the recommended next action.

Do not include credentials, private financial information, full chat
transcripts, or temporary details that do not help resume the work.

## Session handoff routine

1. Start by reading `PROJECT_STATE.md` and the most recent session log.
2. Keep one concrete active slice with an observable completion criterion.
3. Before stopping, reconcile the progress table with actual files and results.
   Distinguish implemented, validated, accepted, blocked, and deferred work.
4. Add a session log with validation evidence and an exact next action. Do not
   present an older test result as a fresh test run.
5. Commit authorized, reviewed work and report the commit in the handoff. If
   work remains uncommitted, say so explicitly. Push only to an authorized remote.

Git tracks committed file changes, not ignored runtime data or an off-device
backup. Keep private research/account data outside these logs.
