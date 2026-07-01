# Experiment 0003: Decision-monitoring signal quality

- Status: Planned
- Baseline: Follow-up criteria and alerts are not persisted

## Hypothesis

Explicit deterministic monitoring rules will reduce missed or irreproducible
follow-up conditions without creating duplicate alerts or weakening human
authority.

## Metrics

- supported-rule truth-table accuracy;
- temporal-boundary violations;
- duplicate evaluations and alerts;
- invalid or ineligible monitor rejection rate;
- artifact reconstruction after restart;
- open-to-acknowledged event integrity; and
- number of alerts requiring correction during fixture review.

## Acceptance threshold

- Every rule fixture matches its expected trigger state.
- No observation after `as_of` affects a result.
- Repeated identical evaluation returns one artifact and one alert per triggered
  rule.
- Ineligible dispositions, malformed rules, invalid thresholds, and missing
  histories fail explicitly.
- Acknowledgement is append-only and cannot erase or mutate the alert evidence.
- No monitoring command calls a model, scheduler, notification service, or
  broker.

## Removal path

If rules are noisy or cannot be reconstructed, keep the underlying research
decision records and remove the monitoring commands and tables before adding
automation or delivery integrations.
