# On-request opportunity radar v1

Status: manual research workflow with validated briefing coverage; not a
continuous scanner, market-wide ranking model, or automated recommendation.

Each daily briefing includes two independent coverage declarations: portfolio
review and opportunity scan. Legacy editions default to scan not run. Completed
means the declared finite universe was reviewed, not that due diligence is done.
Use partial when any declared company remains unchecked. Record failures rather
than silently dropping names. Retain scan time separately from account time.

## Repeatable pass

1. Declare a small universe before fetching data and explain selection. Start
   with four liquid U.S.-listed companies across different business areas;
   rotate names in subsequent editions and retain why names entered or exited.
   This is a purposive sample, not a claim to find the best market opportunities.
2. Retrieve quotes with their source times, official previous-session closes,
   and valuation metadata through authorized read-only tools. Missing values
   remain unknown. Snapshot P/E is only triage, not fair value; do not annualize
   one quarter or assume a fall from a high makes a stock cheap.
3. Read dated issuer/SEC releases for growth, cash flow, catalysts and risks.
   Distinguish company claims, verified facts and our inferences. Record gaps.
4. Retain all reviewed names, including deferred/rejected names, in a private
   dated scan artifact with raw broker observations and source links. Show at
   most four concise cards: evidence, valuation, risk, portfolio fit, next gate.
5. Prioritize at most two for the existing SEC/evidence research workflow.
   A scout card is not a persisted research-company run or an approved memo.
   Require normalized cash-flow valuation, downside scenario, portfolio impact,
   refreshed prices and human review before any trade proposal. No allocation
   is invented when those gates are incomplete.
6. Archive the prior briefing before publishing coverage and candidate cards.
   Do not change the account observation timestamp when only research changes.

## How we will test value

Keep timestamped selections AND deferrals unchanged. Track evidence corrections,
time spent per useful thesis, completed valuations and rejected false positives.
At 30/90 days, evaluate a preregistered equal-weight paper shortlist against SPY
over identical dates using adjusted prices, with explicit entry timing and
cost assumptions; retain losers and avoid look-ahead. Separately evaluate thesis
accuracy, not just price movement. This evaluation is planned, not implemented;
one successful pick would not demonstrate an edge. No profit target.

No scheduler, external saved scanner, broker alert, paid feed, new model, or trade
is created by this workflow. Private artifacts remain Git-ignored. Existing
SQLAlchemy persistence stays canonical for full research runs; no new database.
