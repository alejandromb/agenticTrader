# ADR-0016: Scope Milestone 6 as a unified operator workspace

- Status: Accepted
- Date: 2026-07-01

## Context

Dashboard v1 makes company research and disposition usable, but the accepted
quantitative, monitoring, alert, and research-refresh workflows remain CLI-only.
The user still needs to copy artifact IDs and construct commands to use most of
the platform.

Duplicating those engines in browser code would weaken validation and lineage.
Uploading inputs also creates new size, encoding, and trust-boundary concerns.

## Decision

Milestone 6 will make the dashboard the unified local operator workspace for all
accepted capabilities:

1. import exact price-dataset bytes with source and adjustment metadata;
2. run persisted research screens;
3. analyze hypothetical holdings and run versioned backtests;
4. create and evaluate human-defined monitors;
5. list and acknowledge alerts; and
6. compare completed research runs, inspect review packets, and record a human
   review outcome.

Every web operation delegates to the existing domain service or repository.
The HTTP layer performs transport validation only and never reimplements
financial calculations, eligibility, temporal semantics, idempotency, or human
authority rules.

Binary file inputs are base64-encoded in same-origin JSON, decoded with strict
validation, and passed as exact bytes to the domain layer. Request size remains
bounded. Read APIs expose artifact IDs and lineage metadata, never secret values
or arbitrary server files.

## Explicit exclusions

- remote access, authentication accounts, or multi-user collaboration;
- live data feeds, background jobs, scheduling, or notifications;
- editing or deleting immutable datasets, reviews, monitors, or alerts;
- model-generated thresholds, portfolio actions, brokerage, or execution; and
- a separate JavaScript implementation of domain rules.

## Acceptance criteria

Milestone 6 is accepted when HTTP and browser workflows can import a fixture
price file, screen research, analyze holdings, run a cost-aware backtest, create
and evaluate a monitor, acknowledge its alert, compare two eligible research
runs, and record a review outcome. Tests must prove exact-byte preservation,
request-token enforcement, invalid-input rejection, persisted reconstruction,
and delegation to the accepted domain semantics. The full suite and responsive
browser audit must pass without adding execution authority.
