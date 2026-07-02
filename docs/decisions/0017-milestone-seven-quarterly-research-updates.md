# ADR-0017: Scope Milestone 7 as period-safe quarterly research updates

- Status: Accepted
- Date: 2026-07-01

## Context

The research pipeline and dashboard currently analyze only annual Form 10-K
filings. Monitoring and research-refresh reviews therefore cannot incorporate
issuer financial updates during the year. Form 10-Q data introduces accounting
risks that annual extraction does not: one filing can contain both discrete
three-month and cumulative year-to-date duration facts, cash-flow statements are
usually cumulative, and quarterly filings do not repeat the complete annual
business and risk narrative.

## Decision

Milestone 7 will add explicit `10-Q` research alongside the existing default
`10-K` workflow:

1. users choose the filing form; the system never silently substitutes one;
2. discrete income-statement facts use approximately three-month contexts;
3. cash-flow and capital-allocation duration facts use the longest valid
   year-to-date context ending on the filing report date;
4. instant balance-sheet facts use the exact report date;
5. every claim retains period start/end, fiscal period, form, and accession;
6. comparisons and calculations require compatible accounting periods;
7. quarterly cash flow is not annualized and does not feed annual DCF
   sensitivities;
8. missing annual business/risk context remains an explicit limitation; and
9. completed quarterly memos participate in the existing disposition,
   monitoring, screening, and refresh-review workflows.

Same-period cross-accession audits compare only the same filing form. A quarterly
value is never compared with an annual value as though it were a revision.

## Explicit exclusions

- earnings-call transcripts, press releases, guidance, estimates, or news;
- trailing-twelve-month synthesis or annualization;
- quarter-over-quarter comparison when fiscal seasonality differs;
- automatic filing polling, scheduling, or notifications;
- conversational/MCP operation; and
- portfolio action, brokerage, or execution.

## Acceptance criteria

Milestone 7 is accepted when fixtures prove unambiguous discrete-quarter,
year-to-date, and instant selection; incompatible periods cannot enter one
calculation; 10-K behavior remains unchanged; CLI and dashboard can request a
10-Q explicitly; a complete mocked quarterly research run persists claims,
limitations, analysis, and memo; refresh-review compatibility is demonstrated;
and one live SEC discovery/extraction smoke test confirms current issuer data
without requiring a paid model call.
