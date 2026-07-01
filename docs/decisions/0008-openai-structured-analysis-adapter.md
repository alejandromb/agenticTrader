# ADR-0008: Use OpenAI Responses with structured analysis output

- Status: Accepted
- Date: 2026-06-30

## Context

The deterministic ingestion pipeline produces validated, evidence-linked
candidate facts. The first non-deterministic stage must analyze those facts
without weakening provenance, inventing new evidence, or obtaining investment
or execution authority.

OpenAI is the selected initial model provider. The provider interface must be
replaceable, versioned, and testable without live API calls.

## Decision

The first model-backed financial-analysis stage will use:

- the official OpenAI Python SDK;
- the Responses API;
- Structured Outputs parsed into a strict Pydantic contract;
- pinned model `gpt-5.4-2026-03-05` by default;
- runtime override through `OPENAI_MODEL`; and
- runtime authentication through `OPENAI_API_KEY` only.

The model receives only validated candidate claims and the investment question.
It returns a financial assessment, strengths, concerns, and uncertainties. Every
analytical point must reference input claim IDs. References to unknown claims
invalidate the entire output.

The model does not receive broker tools, credentials, unrestricted web access,
or permission to create evidence. It cannot record a human disposition or
recommend an executable order.

The pinned model may be changed only through an explicit decision and evaluation
against retained fixtures. Configuration can override the model for experiments,
but the actual model identifier is recorded with every artifact.

## Consequences

- Structured outputs reduce parsing ambiguity and are validated twice: by the
  SDK contract and by domain-level claim-reference checks.
- A pinned snapshot improves repeatability compared with a moving alias.
- OpenAI becomes an external runtime dependency with cost, latency, availability,
  and data-governance considerations.
- API keys remain outside the repository and persistence layer.
- Model quality must be evaluated; schema compliance does not establish
  analytical correctness.

## Alternatives considered

### Use the moving `gpt-5.4` alias

Rejected as the default because behavior can change without a repository change.
It remains available as an explicit experiment override.

### Use GPT-5.5 initially

Deferred as the initial default. It is the current flagship and should be part
of later quality evaluation, but GPT-5.4 provides a more economical baseline for
the first bounded professional-analysis stage.

### Use the Agents SDK

Deferred because version one has an explicit workflow and does not need dynamic
handoffs or autonomous tool use.

### Accept free-form model prose

Rejected because it would weaken validation, lineage, and downstream memo
assembly.
