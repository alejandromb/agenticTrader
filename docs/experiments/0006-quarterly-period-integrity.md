# Experiment 0006: Quarterly period integrity

- Status: Accepted
- Baseline: Annual 10-K research only

## Hypothesis

Explicit duration-shape selection and compatible-period calculation rules can
add useful quarterly updates without period mixing or false annualization.

## Metrics

- discrete/YTD/instant fixture selection accuracy;
- incompatible calculation pairs admitted;
- annual regression failures;
- unsupported annualization or DCF outputs;
- claim and limitation lineage completeness;
- refresh-review period-shift fidelity; and
- live SEC extraction success without paid analysis.

## Acceptance threshold

- All fixture contexts select the documented fact.
- Zero calculations combine incompatible start/end dates.
- Quarterly output contains no annualized or DCF claim.
- Annual tests remain unchanged and passing.
- Mocked end-to-end 10-Q workflow reaches human disposition with explicit gaps.
- Live SEC smoke evidence retains accession, form, fiscal period, and dates.

## Result

- 118 tests passed, including fixture selection, incompatible-period rejection,
  annual regression coverage, dashboard form propagation, and a mocked 10-Q run.
- The mocked 10-Q run reached `awaiting_human_disposition`, retained explicit
  quarterly limitations, and created zero valuation-scenario claims.
- A read-only live SEC smoke test selected Apple accession
  `0000320193-26-000013`, Form 10-Q, report date `2026-03-28`.
- Revenue, net income, and operating income used `2025-12-28` through
  `2026-03-28`; cash-flow metrics used `2025-09-28` through `2026-03-28`;
  balance-sheet metrics used the exact `2026-03-28` instant.
- The live smoke test did not call OpenAI or write a research run.
- Browser visual verification was unavailable because the browser controller
  rejected the localhost URL. Dashboard HTTP and asset integration tests passed.

## Conclusion

Accepted. Explicit period-shape rules add quarterly evidence without admitting
period mixing, annualization, or quarterly-derived DCF scenarios.
