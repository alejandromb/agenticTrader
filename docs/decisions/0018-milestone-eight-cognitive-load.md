# ADR-0018: Scope Milestone 8 as dashboard cognitive-load reduction

- Status: Accepted
- Date: 2026-07-02

## Context

The unified dashboard makes the system functional, but exposing research,
quantitative tools, monitoring, alerts, and reviews together can overwhelm the
operator. Adding more charts would increase surface area without proving that
decisions become faster or better.

## Decision

Milestone 8 will simplify the existing dashboard around investment questions
and progressive disclosure. The default experience will emphasize the current
decision, its supporting evidence, known limitations, and the next human action.
Advanced tools remain available but do not compete with the primary workflow.

Every proposed visualization must identify:

1. the investment question it answers;
2. why it is faster or less error-prone than concise text;
3. the evidence and limitations it preserves; and
4. the observable outcome used to judge whether it reduces cognitive load.

## Deferred dashboard backlog

- portfolio heatmaps and timeline;
- sector and factor exposure;
- correlation matrix;
- historical research accuracy and decision-quality metrics;
- watchlist visualization;
- cross-company comparison; and
- risk-concentration visualization.

These are candidates, not commitments. Each requires a separate measured-value
case before implementation.

## Acceptance criteria

Milestone 8 is accepted when the primary research journey is visibly simpler,
advanced workspaces use progressive disclosure, existing capabilities remain
reachable, evidence and known limitations remain prominent, keyboard/mobile
behavior remains usable, and a task-based evaluation shows fewer navigation or
interpretation steps without workflow regressions.

## Explicit exclusions

- new portfolio analytics or visualizations;
- conversational/MCP operation;
- automated investment decisions; and
- broker or execution integration.
