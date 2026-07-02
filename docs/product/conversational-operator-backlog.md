# Conversational Research Operator — Deferred Requirement

- Status: Deferred after Milestone 6
- Recorded: 2026-07-01

## User need

Operate the platform through natural-language conversation while retaining the
same deterministic research, quantitative, monitoring, and review services that
power the dashboard and CLI.

## Required safeguards before implementation

- persistent chat sessions with explicit artifact and tool-call lineage;
- read-only questions clearly separated from paid or state-changing tools;
- confirmation immediately before paid research and human-record mutations;
- no conversational authority to select dispositions, alter portfolios, create
  orders, or execute trades;
- bounded context retrieval rather than silently treating chat memory as fact;
- measured hallucination, tool-selection, latency, and cost performance; and
- stable tool contracts before considering MCP as an integration surface.

## Deferral reason

The deterministic operator workflows are now available in the unified
dashboard. Real usage should first identify which tasks benefit from
conversation and whether chat improves completion/error rates enough to justify
the additional model cost and authority surface under ADR-0010.
