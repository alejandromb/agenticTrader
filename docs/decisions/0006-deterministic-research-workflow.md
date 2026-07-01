# ADR-0006: Use a deterministic, resumable research workflow

- Status: Accepted
- Date: 2026-06-30

## Context

The project summary proposes specialized analyst roles. Those roles could be
implemented as autonomous agents that choose their own tasks and communication
paths, or as controlled stages in an explicit workflow. Version one must be
auditable, resumable after interruption, and capable of explaining which inputs
produced each output.

## Decision

Version one will use a deterministic state machine to orchestrate research.
Role-specific model calls are bounded workflow stages, not independently
authoritative agents.

The initial states are:

```text
draft
  -> collecting_evidence
  -> evidence_ready
  -> analyzing
  -> challenging
  -> synthesizing
  -> validating
  -> awaiting_human_disposition
  -> complete
```

Any processing state may transition to `failed`. A failed run records its last
completed stage and can resume from an explicitly chosen safe checkpoint.

The workflow stages are:

1. **Intake:** Normalize the company, question, horizon, and `as_of` boundary.
2. **Evidence collection:** Acquire and catalog admissible sources.
3. **Extraction:** Produce candidate facts and calculations with evidence links.
4. **Analysis:** Produce business, financial, valuation, and risk artifacts.
5. **Challenge:** Test the thesis, identify contradictory evidence, and expose
   unsupported conclusions.
6. **Synthesis:** Assemble the canonical investment memo.
7. **Validation:** Enforce schema, reference, evidence, and time-boundary rules.
8. **Human disposition:** Await and record the user's decision separately from
   the analytical recommendation.

Each stage receives versioned structured input and produces versioned structured
output. Stage transitions, prompt versions, model identifiers, timestamps, and
errors are recorded. Model output cannot directly mutate evidence or mark its
own validation as successful.

Independent analysis stages may run concurrently when they depend on the same
completed evidence snapshot, but completion order cannot alter the synthesis
contract.

## Consequences

- Work can resume safely from a known state.
- Runs are easier to reproduce, inspect, and compare.
- Specialized perspectives remain possible without uncontrolled delegation.
- The workflow may be less flexible than an autonomous multi-agent system.
- Adding or reordering stages requires explicit workflow versioning.
- Persistent run and stage state become core domain concepts.

## Alternatives considered

### Autonomous multi-agent collaboration

Rejected for version one because dynamic delegation and unconstrained message
passing make provenance, replay, failure recovery, and cost control harder.

### One model call that writes the entire memo

Rejected because evidence collection, competing analysis, and validation would
be conflated, making unsupported claims harder to detect.

### External workflow engine from day one

Deferred. The initial state machine is small enough to implement in application
code and persistence. A durable workflow platform can be adopted later if
operational requirements justify it.
