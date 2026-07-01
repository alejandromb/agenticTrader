# ADR-0011: Scope version two as a complete research decision record

- Status: Accepted
- Date: 2026-07-01

## Context

Version one established an auditable SEC-to-analysis financial pipeline. The
project roadmap also calls for company analysis, valuation, competing theses,
and written investment decisions before portfolio analytics or automation.
Moving directly to screeners, backtesting, or broker integration would optimize
selection and execution before the underlying decision record is complete.

## Decision

Version two will extend the one-company U.S. equities workflow into a complete
research decision record. It will add:

1. source-linked business-model, strategy, and material-risk evidence from the
   selected Form 10-K;
2. structured business-quality and risk analysis with claim-level references;
3. deterministic valuation scenarios with explicit formulas, assumptions,
   ranges, and sensitivity—not a single authoritative price target;
4. explicit bull, base, and bear cases plus a devil's-advocate challenge;
5. a canonical, versioned investment memo that retains all input lineage and
   known limitations; and
6. a separately persisted human disposition: `investigate`, `watch`, `reject`,
   or `consider_for_portfolio`.

The system may recommend a disposition but cannot set the human disposition.
Valuation inputs that are not issuer-reported must retain their source and
`as_of` boundary. Assumptions are never presented as facts.

Version two excludes:

- screeners and universe ranking;
- portfolio construction, allocation, or rebalancing;
- backtesting and technical signals;
- brokerage credentials, order intent, or execution;
- options, cryptocurrency, and non-U.S. securities; and
- autonomous decisions.

## Acceptance criteria

Version two is accepted only when one command can produce and later retrieve a
validated memo containing financial, business, risk, valuation, bull/base/bear,
challenge, limitation, and provenance sections; a separate command can record a
human disposition without mutating the memo; and every material factual or
calculated statement is traceable to captured evidence or explicit assumptions.

The evaluation must compare Version 2 against the Version 1 baseline using the
same issuer and question. It must pass all lineage gates and improve decision
usefulness without introducing unsupported facts or execution authority.

## Consequences

- The research artifact becomes useful as a durable investment-committee record.
- Valuation and qualitative analysis require new contracts and evaluation data.
- Portfolio and execution work remain blocked by scope, not merely deferred by
  implementation order.
