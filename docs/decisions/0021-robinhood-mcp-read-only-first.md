# ADR-0021: Treat Robinhood MCP as portfolio context before execution

- Status: Accepted
- Date: 2026-09-07

## Context

Robinhood exposes an official Trading MCP endpoint at
`https://agent.robinhood.com/mcp/trading`. Its documentation says Codex can
connect to the endpoint through Settings → MCP servers → Streamable HTTP.

The same documentation says a connected agent can read Robinhood accounts,
positions, balances, transactions, order history, watchlists, and scans. It also
says the agent can place orders in the dedicated Robinhood Agentic account.

That creates a useful portfolio-context opportunity, but it also introduces
live-money execution risk. Agentic Trading's current architecture is a research
copilot with human authority, evidence-backed memos, durable decision records,
and explicit safety boundaries.

## Decision

Robinhood MCP integration will be treated as read-only portfolio context first.
The initial product use is to import or inspect portfolio state so the research
copilot can answer questions such as:

1. how concentrated the portfolio is by ticker, sector, and theme;
2. whether new buys increase an already-overweight exposure;
3. how margin, buying power, and cash affect decision risk;
4. whether a research memo has enough evidence to support watch, add, trim, or
   reject as a human disposition; and
5. which holdings need fresh evidence or monitoring rules.

Agentic Trading must not place trades, rebalance, day trade, or automate orders
through Robinhood by default.

## Required execution preconditions

Any future Robinhood execution capability requires a separate ADR and product
contract before implementation. That later contract must include:

- an explicit order-intent object separate from research memos;
- preview-before-place semantics;
- human approval for every order unless the user separately accepts a narrow
  automation policy;
- per-order, per-day, and per-symbol limits;
- margin-usage safeguards;
- position-concentration checks;
- idempotency keys for every order intent;
- append-only audit logging of request, preview, approval, submission, and
  broker result;
- broker reconciliation after submission; and
- a kill-switch / disconnect procedure.

## Explicit exclusions

- No Robinhood credentials, OAuth tokens, account numbers, or portfolio exports
  may be committed to Git.
- No order-placement tool may be called from ordinary research workflows.
- No day-trading feature is part of version one.
- No automatic liquidation, rebalancing, or recurring-buy modification may occur
  without explicit user approval at the action level.

## Consequences

This preserves the value of Robinhood Agentic Trading for portfolio awareness
without weakening the core safety philosophy. The system can become more useful
immediately by understanding real holdings, while execution remains a later,
separately governed capability.
