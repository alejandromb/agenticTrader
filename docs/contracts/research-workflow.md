# Research Workflow Contract

## Run identity

Every research run has a stable ID, workflow version, memo ID, current state,
creation time, update time, and `as_of` boundary.

## Transition rules

- Transitions follow ADR-0006 and are recorded as append-only events.
- A stage starts only when its required predecessor artifacts are valid.
- Repeating a stage creates a new attempt; it does not overwrite prior output.
- Only validated artifacts can become inputs to a later stage.
- `failed` records the stage, attempt, error category, and safe retry status.
- Human disposition is not a model-owned transition.

## Stage artifact envelope

Every stage output is wrapped with:

- run ID, stage name, and attempt number;
- artifact schema name and version;
- input artifact identifiers;
- evidence-snapshot identifier;
- prompt and model identifiers when a model is used;
- start and completion timestamps;
- validation result; and
- content hash.

## Determinism boundary

Model generation is probabilistic. Workflow determinism means that state
transitions, accepted inputs, validation rules, and artifact lineage are
explicit and repeatable. It does not claim identical generated prose across
runs.

## Failure categories

- `source_unavailable`
- `source_rejected`
- `extraction_failed`
- `model_failed`
- `validation_failed`
- `time_boundary_violation`
- `persistence_failed`
- `cancelled`

Failure details must be safe to persist and must not expose credentials.
