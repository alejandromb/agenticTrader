# ADR-0015: Add a loopback-only local dashboard

- Status: Accepted
- Date: 2026-07-01

## Context

The research engine is usable through the CLI but the primary workflow requires
users to copy run IDs, read large JSON payloads, and remember command syntax.
That is acceptable for engineering verification, not for routine research.

Adding a dashboard must not create new investment authority, expose secrets,
silently broaden network access, or fork business rules into a second system.

## Decision

Add a dependency-free local web dashboard served by the Python application. The
first surface will:

1. start only on an explicit CLI command;
2. bind only to a loopback address;
3. show configuration readiness without exposing secret values;
4. list and open persisted research runs and canonical memo content;
5. launch the existing company-research service from a clearly labeled form;
6. record an eligible human disposition through the existing append-only
   repository and workflow transition; and
7. use the same database, artifacts, validation, and service layer as the CLI.

State-changing requests require an unguessable per-process token delivered in
the initial same-origin page and sent in a custom request header. Request bodies
are size-bounded, JSON is validated, external assets are not loaded, and secret
environment values are never returned.

The server uses the standard library for this initial local surface. A larger web
framework will be adopted only when routing, concurrency, authentication, or
deployment requirements demonstrate a measurable need.

## Explicit exclusions

- LAN/public binding, remote access, accounts, or multi-user authentication;
- background jobs, scheduling, live updates, or notification delivery;
- new research, disposition, portfolio, monitoring, or execution authority;
- broker or DiveTrader integration; and
- third-party scripts, fonts, analytics, or hosted assets.

## Acceptance criteria

The dashboard is accepted when automated HTTP tests prove loopback enforcement,
secret-safe configuration output, run list/detail reconstruction, request-token
enforcement, input validation, and disposition persistence; browser verification
proves the responsive page renders, navigates saved runs, and exposes the
research and disposition workflows; and the complete regression suite passes.
