# Evaluation: Walmart financial analysis 001

- Date: 2026-07-01
- Company: Walmart Inc.
- Filing: Fiscal 2026 Form 10-K
- Artifact ID: `322fa6a9-8d09-4f30-9871-7ad935b4d171`
- Model: `gpt-5.4-2026-03-05`
- Prompt version: `1.1.0`
- Schema version: `1.0.0`
- Result: Accepted

## Automatic gates

| Gate | Result | Notes |
| --- | --- | --- |
| Structured contract | Pass | Parsed and validated as `FinancialAnalysis`. |
| Claim lineage | Pass | All references resolve to the four persisted Walmart claims. |
| Execution boundary | Pass | No trade, allocation, or return guarantee appears. |
| Numeric support | Pass | All reported numbers match supplied claims. |
| Artifact metadata | Pass | Model, prompt, response ID, schema, and inputs are recorded. |

## Scored criteria

| Criterion | Score | Notes |
| --- | ---: | --- |
| Numerical fidelity | 2 | Revenue, net income, operating cash flow, and assets are accurate. |
| Evidence fidelity | 2 | Derived comparisons are labeled as analysis; missing liabilities remain uncertainty rather than inferred debt. |
| Fact/judgment separation | 2 | Reported facts and interpretations are clearly distinguished. |
| Balance | 2 | Scale, profitability, cash generation, margin pressure, and missing balance-sheet evidence are represented. |
| Uncertainty | 2 | Trend, liabilities, liquidity composition, margin, debt, and segment gaps are explicit. |
| Decision usefulness | 2 | Each evidence gap becomes a concrete next research request. |
| **Total** | **12/12** | Acceptance threshold met. |

## Prompt v1.1 result

The changes derived from the Apple evaluation worked as intended:

- no unsupported attribution qualifier was added to net income;
- total liabilities were not treated as synonymous with debt; and
- derived comparisons were explicitly labeled as analysis.

## Platform finding

Walmart did not expose the generic `us-gaap:Liabilities` concept used by the
minimum snapshot. The first attempt failed safely before any model request. The
workflow was revised so unavailable issuer concepts become explicit evidence
gaps rather than fabricated or silently substituted values.

This artifact was generated immediately before migration `20260701_0005`, which
added first-class persistence for known evidence gaps. The evaluation records
the missing-liabilities context; future artifacts persist it directly.
