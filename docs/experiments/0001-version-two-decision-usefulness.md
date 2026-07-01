# Experiment 0001: Version 2 decision usefulness

- Status: Planned
- Baseline: Accepted Version 1, prompt 1.7, Walmart run
  `de2b6abf-7548-4a56-a40f-c0b83007e39f`

## Limitation

Version 1 explains financial condition and cash allocation but does not produce
a complete business/risk/valuation memo or retain a human disposition.

## Hypothesis

A structured business, risk, valuation, challenge, and disposition workflow
will improve decision usefulness without reducing numerical or evidence
fidelity and without adding execution authority.

## Evaluation

Use the same issuer and a stable investment question. Score both versions on:

- numerical fidelity;
- evidence fidelity;
- assumption/fact separation;
- risk and counterargument coverage;
- valuation transparency;
- limitation coverage;
- decision usefulness;
- latency; and
- model/API cost.

## Acceptance threshold

- Every automatic lineage and safety gate passes.
- No scored quality criterion receives zero.
- Version 2 improves decision usefulness and valuation transparency.
- Numerical and evidence fidelity do not decline from the Version 1 baseline.
- Added latency and cost are recorded, not hidden.

If these thresholds fail, the new stage remains experimental or is removed.
