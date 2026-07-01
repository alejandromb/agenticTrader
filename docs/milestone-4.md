# Milestone 4 Product Contract

## Outcome

Turn eligible human research dispositions into explicit, reproducible monitoring
criteria without adding live feeds, autonomous judgment, or execution.

## Required workflows

```text
create-monitor RUN_ID --name NAME --rules RULES.json
evaluate-monitor MONITOR_ID --dataset DATASET_ID --as-of DATE
list-alerts [--monitor MONITOR_ID] [--status open|acknowledged]
acknowledge-alert ALERT_ID --note NOTE
```

## Rule contract

Rules are a JSON array. Each object requires a stable `rule_id`, supported
`type`, ticker, and decimal threshold.

```json
[
  {"rule_id":"price-floor","type":"price_below","ticker":"AAPL","threshold":"90"},
  {"rule_id":"drawdown","type":"drawdown_at_least","ticker":"AAPL","threshold":"0.20"}
]
```

Supported rule types:

| Type | Trigger condition |
| --- | --- |
| `price_below` | latest adjusted close is strictly below threshold |
| `price_above` | latest adjusted close is strictly above threshold |
| `drawdown_at_least` | decline from the dataset peak through `as_of` is greater than or equal to threshold |

Drawdown thresholds are decimal fractions greater than zero through one. Exact
equality does not trigger strict price rules. All observations are bounded by
`as_of`.

## Eligibility and authority

A monitor can be created only after a human records `watch` or
`consider_for_portfolio` on a completed research run. Rules and thresholds are
human inputs. Evaluation and acknowledgement never change the disposition,
memo, holdings, or any external system.

## Persistence and idempotency

- Monitor definitions are immutable after creation.
- Each evaluation records the monitor, dataset, hash, boundary, results, and
  creation time.
- Monitor/dataset/`as_of` uniquely identifies an evaluation.
- Repeating that request returns the existing evaluation and creates no
  duplicate alert.
- Acknowledgements are append-only human events.

## Non-goals

No scheduler, live feed, notification delivery, LLM call, news monitoring,
automatic research, broker connection, order, or portfolio mutation.
