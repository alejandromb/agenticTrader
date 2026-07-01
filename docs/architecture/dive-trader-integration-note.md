# DiveTrader integration note

- Recorded: 2026-07-01
- Source: Architect feedback supplied by the project owner
- Related sibling project: `../diveTrader`
- Status: Future integration candidate; not part of Agentic Trading v1

## Architectural position

DiveTrader can eventually become part of the broader Agentic Trading system,
but it should remain a separate execution sandbox and prototype for now. It
must not be merged directly into the core research architecture or treated as
ready for live-money execution.

Its canonical designation is:

> Potential future execution adapter for Agentic Trading, currently suitable
> only for paper-trading experiments and UI/broker-integration reference.

The projects should mature independently before any integration work:

- Agentic Trading must first mature its research integrity, evidence lineage,
  decision records, evaluation, and human-authority boundaries.
- DiveTrader must independently harden execution safety, broker state handling,
  operational controls, and paper/live separation.

This preserves useful prototype work without allowing a trading application to
weaken the safety philosophy or evidence standards of the main project.

Agentic Trading remains the brain, research, and decision-support layer. Its
responsibilities include deterministic evidence collection, source-linked
claims, structured investment memos, watchlists, strategy hypotheses, risk
notes, and human-reviewed recommendations.

DiveTrader is a candidate broker-execution and portfolio-operations laboratory.
It reportedly contains useful prototype capabilities:

- React dashboard;
- FastAPI backend;
- Alpaca integration;
- strategy management and backtesting;
- risk and performance views; and
- manual trading workflows.

These capabilities are described as development and paper-trading functionality,
not production-ready or approved for live funds.

## Primary architecture risk

DiveTrader reportedly has two overlapping backend generations: a legacy
SQLAlchemy/v1 implementation and a newer SQLModel/v2 implementation, with the
frontend consuming both. This is the highest-priority architecture issue to
resolve before production integration or live-money consideration.

## Required execution boundary

The intended long-term boundary is:

```text
Agentic Trading Research Copilot
  - filings, news, and research ingestion
  - structured memos and claim-level evidence
  - watchlists, risk notes, and trade hypotheses
  - human-reviewed recommendation
                 |
                 v
Order Intent and Human Review
  - proposed action and rationale
  - evidence links and risk limits
  - explicit human approval
                 |
                 v
DiveTrader Execution Layer
  - Alpaca adapter
  - strict paper/live separation
  - order submission and position synchronization
  - audit log and broker reconciliation
```

Agentic Trading must never call a broker directly. Any future integration must
produce an order-intent artifact first and require explicit human approval.

## Preconditions for future integration

Before DiveTrader can become an execution layer, it needs:

1. one canonical API and one canonical model/persistence system;
2. a centralized order-intent workflow;
3. pre-trade risk and authorization checks;
4. strict paper/live environment and credential separation;
5. idempotent order submission;
6. an append-only audit trail;
7. broker order, fill, cash, and position reconciliation;
8. failure recovery and duplicate-order prevention; and
9. production security and operational-readiness review.

## Current decision

No DiveTrader code is imported or merged into Agentic Trading. No brokerage or
execution work enters the version-one roadmap. The sibling project may be
inspected later as input to a separate architecture review and ADR; integration
requires explicit authorization and measured safety criteria.
