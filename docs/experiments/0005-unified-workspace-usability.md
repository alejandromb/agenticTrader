# Experiment 0005: Unified workspace usability

- Status: Accepted
- Baseline: Research/disposition are graphical; all later workflows require CLI IDs

## Hypothesis

A single dashboard over the accepted domain services will make the complete
research loop operable without reducing deterministic correctness, lineage, or
human authority.

## Metrics

- completed end-to-end fixture workflows without terminal commands;
- exact-byte upload fidelity;
- domain/API result equivalence;
- invalid-input and authorization rejection accuracy;
- missing artifact identity or lineage fields;
- browser errors and responsive-layout failures; and
- execution-boundary violations.

## Acceptance threshold

- Every Milestone 3–5 workflow completes through the dashboard HTTP surface.
- Uploaded fixtures retain their original SHA-256 and byte content.
- API outputs retain the accepted domain artifact IDs and warnings.
- Invalid request tokens, malformed uploads, and domain-invalid parameters fail.
- Desktop and mobile operator surfaces remain navigable without page overflow.
- No broker, order, allocation, or autonomous disposition path is introduced.

## Removal path

If a dashboard workflow diverges from its CLI/domain result, remove that route
and UI form while retaining the accepted domain service and artifact history.

## Result

- HTTP lifecycle tests imported exact fixture bytes, persisted the matching
  source artifact, screened research, analyzed holdings, and ran the versioned
  cost-aware backtest.
- The same dashboard lifecycle completed eligible disposition, monitor creation,
  evaluation, alert listing, and human acknowledgement.
- A separate two-run fixture completed review creation, retrieval, and one human
  review outcome through the HTTP surface.
- Strict base64, request-token, domain parameter, and eligibility failures
  remained explicit.
- Browser verification against the real database rendered all four workspaces,
  correct empty/eligible states, and no console warnings or errors.
- The 390px audit retained exact viewport width and usable fixed navigation.
- Static and dependency inspection found no order, broker, allocation, or
  autonomous disposition path.
