# Experiment 0003: Decision-monitoring signal quality

- Status: Accepted
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

## Result

- Fixture price-above, price-below, equality, and drawdown cases matched the
  documented truth conditions.
- An earlier `as_of` boundary excluded later observations and changed the rule
  result as expected.
- Repeating the identical request after constructing a new service instance
  returned the original evaluation and the same two alerts.
- Rejected dispositions, malformed rule shapes, unsupported rule types,
  out-of-range drawdowns, and duplicate acknowledgement attempts failed
  explicitly.
- Alert evidence remained immutable; acknowledgement status was derived from a
  separate append-only event.
- Static scope review found no model, scheduler, notification, broker, order,
  or portfolio-mutation dependency in the monitoring module.
