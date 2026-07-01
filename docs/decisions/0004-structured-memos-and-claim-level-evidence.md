# ADR-0004: Use structured memos with claim-level evidence

- Status: Accepted
- Date: 2026-06-30

## Context

Version one produces investment memos from public evidence. Free-form reports
alone are difficult to validate, compare, audit, or evaluate over time. A memo
also needs to distinguish external facts from calculations, assumptions, and
analytical judgments so that fluent prose is not mistaken for verified truth.

## Decision

Each investment memo will be stored as a structured, versioned document with a
human-readable rendering derived from that structure.

Material assertions will be represented as individual claims. Each claim has a
type:

- `fact`: an externally verifiable statement;
- `calculation`: a value derived from stated inputs and a stated method;
- `assumption`: an input accepted for the analysis but not established as fact;
  or
- `opinion`: an analytical interpretation or judgment.

Facts require at least one evidence reference. Calculations require their input
claim references and method. Assumptions and opinions require explicit
rationale and must not be presented as sourced facts.

Evidence records identify a captured source, publication and retrieval times
when known, the relevant location within the source, and a short supporting
excerpt or normalized data value. Citations point to evidence records rather
than only to a URL.

Every memo includes its scope, as-of time, company identity, investment
question, thesis, counter-thesis, risks, uncertainties, valuation discussion,
claim and evidence registries, and human disposition. Unknown information is
represented explicitly rather than invented or silently omitted.

The canonical interchange format for version one is JSON validated against a
versioned JSON Schema. This specifies the data contract without determining the
application language, database, or user interface.

## Consequences

- Claims can be audited and evaluated independently from the prose around them.
- Renderers and interfaces can change without changing the canonical memo.
- Schema evolution must be explicit and backward compatibility considered.
- Agent outputs require normalization and validation before persistence.
- Claim-level evidence adds complexity compared with ordinary Markdown reports.

## Alternatives considered

### Store only Markdown reports

Rejected as the canonical format because key fields and citations would be
difficult to validate reliably. Markdown may still be generated as a view.

### Require citations only at the section level

Rejected because a section may mix facts, assumptions, and opinions, making it
unclear which source supports which statement.

### Treat every statement as a sourced fact

Rejected because investment analysis necessarily includes calculations,
assumptions, and judgments that should remain visibly distinct from facts.
