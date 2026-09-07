# Session: Exact-filing coverage and scoped capital expenditure

## Outcome

- Quarterly research explicitly rejects an SEC company-facts response with no
  observations for the selected accession. It does not substitute an older filing.
- Added a narrowly scoped ISRG CIK/accession mapping for ProductiveAssets to
  cash capex, verified against the original statement's PP&E purchase label:
  https://www.sec.gov/Archives/edgar/data/1035267/000103526726000058/isrg-20260630.htm
- The mapped fact retains its original taxonomy concept and YTD period in claims
  and history. No global ProductiveAssets equivalence is assumed.
- Live testing exposed an empty-result fallback defect: the standard tag could
  exist historically without selected-filing facts and suppress aliases. Fixed
  this and made the regression fixture reproduce that situation.

## Verification

159 tests passed in 9.21 seconds with loopback access; changed-file Ruff and
git diff whitespace checks passed. Restricted execution initially failed eight
HTTP tests because they require loopback sockets; the permitted rerun passed.
Tests include positive mapping, original provenance, YTD/history consistency,
wrong issuer, wrong accession, empty primary-tag filing coverage, and unavailable
accession diagnostics.

Live Visa rerun correctly reported no observations for its selected July filing.
Final live ISRG rerun persisted cash capex and the $1.7570B six-month simple
free-cash-flow calculation with claim lineage; capex is no longer a missing
evidence gap. The memo remains awaiting human disposition and explicitly
distinguishes this approximation from owner earnings. This demonstrates improved
evidence coverage, not improved investment returns or a validated buy signal.
Upstream cause remains unknown. The failure is retained as a failed research run;
the detailed diagnostic is currently CLI output, not a structured failure code.

## Boundaries / next steps

Private run identifiers and investment notes remain in ignored local review
artifacts. Existing memos are not rewritten. No orders or account changes made.
Future filing-specific mappings require fresh evidence review. Generic inline
XBRL fallback and structured persisted failure diagnostics remain unimplemented.
Milestone 11 authorized local read transport remains a separate open item.
