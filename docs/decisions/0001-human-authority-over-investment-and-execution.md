# ADR-0001: Preserve human authority over investment and execution decisions

- Status: Accepted
- Date: 2026-06-30

## Context

Agentic Trading is intended to improve investment research, portfolio analysis,
and decision quality through AI assistance. Investment decisions operate under
uncertainty and can cause financial loss. AI-generated conclusions may be
incorrect, poorly supported, stale, or inconsistent with the investor's actual
objectives and constraints.

The system therefore needs an explicit authority boundary before agent roles,
broker integrations, or automation workflows are designed.

## Decision

Agentic Trading will operate as an advisory investment system. AI agents may:

- gather, normalize, and summarize information;
- produce structured analyses and competing investment theses;
- identify uncertainty, missing evidence, and portfolio risks;
- propose portfolio actions and explain their reasoning; and
- monitor approved positions and decision criteria.

AI agents will not hold final authority to allocate capital or execute trades.
A human must explicitly approve investment decisions and brokerage actions.

Broker integrations, including any Robinhood MCP integration, must enforce this
boundary. Read-only portfolio and market-data operations may be automated.
Order creation or submission must require a distinct human approval step and
must produce an auditable record.

Agent output is treated as untrusted input. It cannot change approval policy,
risk limits, credentials, or execution permissions.

## Consequences

### Benefits

- Accountability remains with the human investor.
- Incorrect or unsupported agent output cannot directly create market exposure.
- Research automation can evolve independently from execution permissions.
- Proposed and approved actions can be compared during later evaluation.
- Broker credentials can be isolated from most of the system.

### Costs and constraints

- The platform cannot provide fully autonomous trading under this architecture.
- Human approval introduces latency and limits unattended operation.
- Approval state and actor identity must be represented explicitly.
- Interfaces must clearly distinguish analysis, proposals, approvals, and
  executed actions.

## Alternatives considered

### Fully autonomous execution

Agents would be permitted to submit orders within configured limits. This was
rejected because it conflicts with the project's investment-committee model and
introduces operational and financial risk before the system has demonstrated
reliable decision quality.

### No brokerage integration

The system would provide research only, leaving execution entirely external.
This remains a viable early implementation stage but was not selected as a
permanent constraint because approved brokerage workflows and reconciliation
may eventually improve auditability and portfolio operations.

## Follow-up decisions

- Define the first product scope and workflows.
- Define approval states and the evidence recorded with each decision.
- Define portfolio risk constraints independently from agent prompts.
- Define the permissions and safety controls for brokerage integrations.
