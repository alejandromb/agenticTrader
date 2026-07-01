# Version Two Acceptance Audit

- Date: 2026-07-01
- Result: Accepted
- Live company: Walmart Inc.
- Live run: `2f58e3d2-0a6b-4c8b-af8f-de5c99137917`
- Analysis artifact: `ce1126d2-bcd7-4ddc-b8bf-d936fd370c42`
- Memo artifact: `51e91be4-d83a-4d24-9ae7-20e51eeadba6`
- Filing accession: `0000104169-26-000055`
- Prompt: `2.1.0`
- Memo schema: `2.0.0`
- Database schema: `20260701_0011`

## Product-contract audit

| Requirement | Evidence | Result |
| --- | --- | --- |
| Business and risk evidence | Live memo contains bounded Item 1 and Item 1A claims | Pass |
| Business-quality analysis | Structured section contains claim-linked operating-model analysis | Pass |
| Material-risk analysis | Risks remain issuer-disclosed possibilities, not asserted events | Pass |
| Valuation sensitivity | Bear/base/bull DCF claims preserve assumptions, formulas, and inputs | Pass |
| Competing cases | Bull, base, bear, and devil's-advocate sections are independently required | Pass |
| Canonical memo | Schema-2.0 memo persisted with 102 claims and 86 evidence records | Pass |
| Known limitations | Missing liabilities, market price, share count, and valuation bridge remain explicit | Pass |
| Human authority | Live memo remains `undecided`; only explicit disposition command can complete it | Pass |
| Saved reconstruction | `show-run` recovers memo, scenarios, valuation, telemetry, and disposition | Pass |
| No execution | No order, sizing, brokerage, or portfolio mutation exists | Pass |

## Quality comparison

The Version 1 Walmart baseline scored 12/12 on financial-analysis quality.
Version 2 retained numerical and evidence fidelity while adding business, risk,
valuation-transparency, competing-case, memo, and decision-record coverage.
Decision usefulness and valuation transparency therefore improved without
weakening the accepted Version 1 financial sections.

The measured Version 2 model request used 20,539 input tokens and 8,473 output
tokens and took 62,241 ms. Version 1 token and latency telemetry was not captured
before instrumentation existed, so no unsupported numeric cost comparison is
claimed. Future experiments now have a durable measured baseline.

## Verification

- Automated suite: 70 tests passed before documentation finalization.
- Structured output and every claim reference validated.
- Memo schema, semantic references, and `as_of` boundaries validated.
- Database migration reached `20260701_0011`.
- Live workflow stopped at `awaiting_human_disposition` as required.
- Human-disposition completion is covered by integration tests and was not
  exercised on the live memo because that decision belongs to the user.
