# ADR-0003: Scope version one as a U.S. equities research copilot

- Status: Accepted
- Date: 2026-06-30

## Context

The long-term vision includes company research, portfolio analysis, risk
management, automation, and brokerage integration. Building these capabilities
simultaneously would make it difficult to validate research quality, establish
reliable data provenance, and maintain the human-authority boundary established
by ADR-0001.

Version one needs a narrow vertical slice that delivers useful output, exercises
the core research workflow, and can be evaluated without creating brokerage or
portfolio risk.

## Decision

Version one will be a research copilot for long-term fundamental analysis of
U.S. publicly traded equities.

The primary workflow is:

1. A user selects one public company and provides an investment question.
2. The system gathers relevant public source material.
3. Specialized analyses examine the company, industry, financial condition,
   risks, and credible counterarguments.
4. The system synthesizes a structured investment memo that distinguishes
   sourced facts, calculations, assumptions, and opinions.
5. Every material factual claim is traceable to its source.
6. The user records one disposition: `investigate`, `watch`, `reject`, or
   `consider_for_portfolio`.
7. The system retains the memo, its inputs, and the human disposition for later
   review.

Version one will support:

- one company per analysis;
- public information only;
- evidence-linked investment memos;
- explicit uncertainty and missing-information reporting;
- bull, bear, and risk perspectives; and
- persistence of research artifacts and human decisions.

Version one will not support:

- order creation or trade execution;
- direct brokerage integration;
- autonomous portfolio allocation or rebalancing;
- options, cryptocurrency, private securities, or non-U.S. listings;
- high-frequency, intraday, or technical-signal trading;
- personalized tax, legal, or suitability advice; or
- claims that returns or market outperformance are guaranteed.

## Success criteria

Version one is successful when a user can produce and later retrieve a coherent
investment memo whose claims can be audited back to captured sources, whose
uncertainties are explicit, and whose analysis is useful enough to support a
human decision about further investigation.

Research quality must be evaluated separately from subsequent stock-price
performance. A favorable outcome does not prove the analysis was sound, and an
unfavorable outcome does not by itself prove it was unsound.

## Consequences

- The initial architecture can focus on source ingestion, analysis contracts,
  synthesis, provenance, persistence, and evaluation.
- Brokerage credentials and execution infrastructure are unnecessary in
  version one.
- Portfolio-wide risk and construction remain future capabilities.
- The memo schema becomes the central contract among research components.
- Expanding to other asset classes or trading horizons requires a later ADR.

## Alternatives considered

### Begin with portfolio tracking

This could deliver immediate monitoring value, but it would not exercise the
project's core research and thesis-building proposition as directly.

### Combine research, portfolio management, and brokerage execution

Rejected for version one because it expands the safety boundary and makes it
harder to evaluate each subsystem independently.

### Begin with quantitative screening and backtesting

Deferred because the stated philosophy prioritizes written theses and
evidence-driven company analysis. Quantitative capabilities can be added after
the research artifact and evaluation model are stable.

## Follow-up decisions

- Define the investment-memo schema and evidence model.
- Define the first source types and data acquisition policy.
- Decide whether version one uses a single orchestrated workflow or multiple
  independently evaluated agents.
- Select the implementation stack after the core contracts are defined.
