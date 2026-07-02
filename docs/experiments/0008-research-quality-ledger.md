# Experiment 0008: Research-quality evaluation ledger

- Status: Accepted
- Baseline: Manual Markdown evaluation records

## Observed limitation

Prior Walmart and Apple evaluations exist as narrative documents, but their
scores, integrity gates, prompt versions, and telemetry cannot be queried or
reconstructed as durable application state.

## Hypothesis

A versioned append-only evaluation ledger will make prompt and workflow changes
measurable without using subsequent stock performance or adding an LLM judge.

## Metrics

- integrity-gate reproducibility after restart;
- invalid or incomplete score records admitted;
- evidence-gap coverage detection accuracy;
- provenance and telemetry completeness;
- mutation of research, memo, or disposition state;
- additional model calls and external requests; and
- operator steps needed to create and retrieve an evaluation.

## Acceptance threshold

- All deterministic gate fixtures match expected results.
- Zero invalid score/rationale records persist.
- Acceptance is derived exactly from the versioned 9-of-12 rule.
- Restart reconstruction matches the original artifact.
- Research and disposition records remain byte-for-byte/field-for-field unchanged.
- No model call, market-data lookup, or external request occurs.

## Result

- Five deterministic gates are recomputed from saved analysis, input-claim,
  candidate-claim, memo, limitation, and provenance records.
- Six criteria require exact 0–2 integer scores and nonempty rationales; malformed,
  incomplete, boolean, or out-of-range inputs are rejected before persistence.
- Acceptance is derived only when all gates pass, no criterion is zero, and the
  total is at least 9 of 12.
- Restart reconstruction matched the original evaluation exactly, and two human
  evaluations of one run persisted as distinct append-only records.
- Tests confirmed evaluation did not change run state or `updated_at`.
- CLI create/list and dashboard create/list/inspection paths preserve complete
  score, rationale, gate, rubric, prompt, model, schema, token, and latency data.
- The full suite passed with 128 tests. JavaScript syntax and Python lint checks
  passed.
- Real-database browser inspection confirmed a collapsed quality ledger, six
  rubric criteria, explicit “artifact quality—not returns” framing, 390px mobile
  containment, and zero console errors.
- No real evaluation was submitted during acceptance because criterion scores
  require human judgment. No model, SEC, market-data, or external request ran.

## Conclusion

Accepted. Research-system changes can now be evaluated as durable process
artifacts without substituting market outcomes or an automated model judge.
