# Version One Acceptance Audit

- Date: 2026-07-01
- Result: Accepted
- Live company: Walmart Inc.
- Live run: `de2b6abf-7548-4a56-a40f-c0b83007e39f`
- Analysis artifact: `a17ccbe2-c5e7-4fd0-87e3-6b6199bfb2e9`
- Filing accession: `0000104169-26-000055`
- Prompt: `1.7.0`
- Database schema: `20260701_0008`

## README requirement audit

| Requirement | Evidence | Result |
| --- | --- | --- |
| Resolve ticker and capture latest 10-K | Live WMT run captured the listed accession and one content-addressed source | Pass |
| Same-filing current and comparative facts | Period-aware extraction and live three-year WMT claims | Pass |
| Source-linked facts and filing statements | 71 persisted claims; claim/source/run foreign keys tested | Pass |
| Deterministic calculations and lineage | 13 calculated claims and 26 persisted input links in the live run | Pass |
| Growth, margins, free cash flow, current ratio | Live v1.7 analysis cited supplied calculation claims for each supported metric | Pass |
| Cash-allocation explanation | Live output covered capex, acquisitions, dividends, repurchases, and debt flows | Pass |
| Quantified capex allocation | Live output preserved table units, years, categories, and totals | Pass |
| Cross-filing revision audit | Visible zero-result live audit; changed-value creation covered by deterministic integration tests | Pass |
| Structured analysis and claim validation | One persisted v1.7 artifact; unknown claim references fail tests | Pass |
| Known limitations | Missing total liabilities was retained in the live known-limitations section | Pass |
| Durable saved-run review | `show-run` recovered claims, formulas, audit count, model, prompt, analysis, and limitations | Pass |
| No execution authority | No broker integration or order workflow exists; ADR-0001 and ADR-0003 remain binding | Pass |

## Verification

- Full automated suite: 62 tests passed.
- Ruff lint: passed.
- Ruff formatting check: passed.
- Database migration reached `20260701_0008`.
- Live run reached `challenging`, the intended handoff to the next controlled
  workflow stage.

Docker image execution is not an acceptance requirement for the documented
local-first version-one workflow. Its daemon metadata issue remains a
non-blocking development-environment follow-up.
