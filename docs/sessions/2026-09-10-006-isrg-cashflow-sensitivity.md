# Session: ISRG cash-flow valuation sensitivity

Verified FY2025 and H1 comparative cash-flow tables against primary SEC filings.
Computed TTM by annual minus prior YTD plus current YTD, not annualizing a
quarter. Separately charged the cash-flow SBC add-back as a conservative proxy;
explicitly not a finished owner-earnings normalization or dilution model.

Implemented Decimal sensitivity and reverse-growth helpers with six tests.
Private source inputs include dated quote, shares, units and assumptions. Report
and input archived by hash and linked to a new deferred candidate event. No
changes to the earlier prospective cohort: do not erase less favorable decisions.

Conclusion is conditional research deferral, not a short/sell recommendation.
Remaining: taxes/working-capital sustainability, lease investment and maintenance
capex, noncontrolling interests, cash/investment income treatment, competitive
underwriting and fresh portfolio fit. No trades or human disposition recorded.

Validation: 232 tests passed with loopback permissions for dashboard tests;
restricted-sandbox socket failures were environmental. Ruff checks and formatting
passed. Regression checking caught an accidental replacement of the existing
valuation API during editing; the original API and tests were restored and the
new helpers added alongside them. Local briefing GET confirmed the updated
deferral and evidence-integrity labels. Private inputs and reports stay excluded
from Git; code, tests and this handoff are versioned.
