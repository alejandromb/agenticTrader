# ADR-0010: Require evidence before adopting additional complexity

- Status: Accepted
- Date: 2026-07-01

## Context

Models, agents, datasets, and signals can make a research system appear more
capable while increasing cost and operational risk without improving decisions.
Feature count is not an outcome measure.

## Decision

Every material capability requires an experiment record before adoption. The
record states:

- the observed failure or limitation;
- a falsifiable improvement hypothesis;
- the current baseline and evaluation dataset;
- metrics for quality, error rate, latency, and cost;
- safeguards against hindsight, leakage, and selection bias;
- acceptance and rejection thresholds; and
- a removal path if the capability fails evaluation.

New sentiment models, LLM calls, agents, and data providers remain experimental
until they demonstrate an outcome improvement against the baseline. Output that
looks more sophisticated is not evidence. Research quality is evaluated
separately from subsequent stock performance unless the experiment explicitly
tests a properly controlled investment hypothesis.

Version one remains a U.S. equities research copilot. This decision does not
authorize brokerage integration, order creation, or autonomous execution.

## Consequences

- Complexity and recurring cost need explicit justification.
- Failed experiments are removed or retained only as documented research.
- Evaluation infrastructure is a product capability, not optional process work.
- A simpler component wins when measured outcomes are equivalent.
