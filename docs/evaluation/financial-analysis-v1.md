# Financial Analysis Evaluation Rubric v1

This rubric evaluates the analytical artifact, not subsequent stock-price
performance. A favorable outcome does not validate weak reasoning, and an
unfavorable outcome does not invalidate a sound process.

## Automatic gates

An artifact fails immediately if any gate fails:

1. It validates against the `FinancialAnalysis` structured-output contract.
2. Every cited claim exists and belongs to the same research run.
3. The recorded model, prompt version, response ID, and input claims are present.
4. It contains no trade instruction, capital allocation, or claim of guaranteed
   return.
5. It introduces no unsupported numeric value as established fact.

## Scored criteria

Score each criterion from 0 to 2:

- **2 — Meets:** Materially correct, explicit, and useful.
- **1 — Partial:** Directionally useful but incomplete or imprecise.
- **0 — Fails:** Incorrect, unsupported, misleading, or absent.

| Criterion | Evaluation question |
| --- | --- |
| Numerical fidelity | Does the analysis accurately interpret the supplied values, units, and periods? |
| Evidence fidelity | Does each point follow from the claims it cites without expanding their meaning? |
| Fact/judgment separation | Are analytical conclusions visibly distinct from reported facts? |
| Balance | Does the analysis identify both strengths and credible concerns? |
| Uncertainty | Does it identify missing evidence that limits the conclusion? |
| Decision usefulness | Does the summary help decide what research should happen next? |

## Acceptance threshold

An analysis is acceptable for the first evaluation when:

- every automatic gate passes;
- no scored criterion receives 0; and
- the total score is at least 9 out of 12.

Acceptance means the artifact can proceed to the challenge stage. It does not
mean the company is suitable for investment.
