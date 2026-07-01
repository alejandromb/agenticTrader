# ADR-0007: Use a Python 3.12 local-first implementation stack

- Status: Accepted
- Date: 2026-06-30

## Context

The initial implementation needs strong support for financial-data processing,
document extraction, model integrations, JSON Schema validation, testing, and a
resumable workflow. Version one is a single-user research copilot and does not
yet require distributed infrastructure or a public web API.

## Decision

The initial application will use:

- Python 3.12 or newer;
- a standard `pyproject.toml` package with source under `src/`;
- JSON Schema as the persisted artifact contract;
- SQLAlchemy 2 as the persistence ORM and repository implementation;
- Alembic for versioned database migrations;
- SQLite for local workflow state and artifact metadata;
- the local filesystem for development evidence artifacts;
- Docker for a reproducible non-root runtime and Docker Compose for local
  service configuration and persistent data volumes;
- `pytest` for tests and `ruff` for linting and formatting; and
- explicit service and repository boundaries so SQLite and local storage can be
  replaced without changing domain contracts.

The standard library is preferred when it provides a clear implementation.
Focused dependencies may be added for standards-compliant schema validation,
HTTP behavior, document parsing, and model-provider clients.

A web framework, background job system, external workflow engine, and
PostgreSQL deployment are deferred until an end-to-end local workflow is
working and their requirements are concrete.

## Consequences

- The implementation aligns with the financial-data and AI tooling ecosystem.
- Local setup and debugging remain simple.
- SQLite supports durable workflow checkpoints without an external service.
- Typed ORM models keep persistence code maintainable and preserve a practical
  path to PostgreSQL.
- Database schema changes require reviewed Alembic migrations.
- Deployment and multi-user concerns are intentionally postponed.
- Code must avoid depending on SQLite-specific behavior at domain boundaries.
- Python and dependency versions must be locked before reproducible deployment.
- Containerized SQLite supports only the single-process version-one topology;
  concurrent or multi-replica deployment requires a database architecture
  review.

## Alternatives considered

### TypeScript and Node.js

Viable for a web-first product, but Python provides a more direct path for the
expected financial analysis, data processing, and model-evaluation workload.

### PostgreSQL from the beginning

Deferred because version one does not yet require concurrent users or a remote
database. The persistence boundary will preserve an upgrade path.

### Adopt a multi-agent framework immediately

Rejected because ADR-0006 defines a small explicit workflow whose contracts and
failure behavior should remain visible in application code.
