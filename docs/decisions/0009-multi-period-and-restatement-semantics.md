# ADR-0009: Preserve filing context in multi-period comparisons

- Status: Accepted
- Date: 2026-07-01

## Context

Later filings can revise previously reported values through restatements,
reclassifications, discontinued operations, or presentation changes. Selecting
facts by fiscal year alone can silently mix incompatible filing contexts.

## Decision

Every fact retains its economic period and filing accession. Current trend
analysis uses current and comparative periods exactly as presented in one
selected filing. An original-as-filed audit view separately retrieves the
period from the filing that first reported it.

If the same concept, unit, and economic period differs across accessions, both
observations are retained and the difference is labeled
`cross_filing_revision`. It is called a restatement only when filing evidence
establishes that classification. Calculations identify exact input claim IDs
and filing view; missing periods are not interpolated.

## Consequences

- Trends remain reproducible within one accounting presentation.
- Original and subsequently revised observations remain auditable.
- Multi-period identity includes accession, concept, unit, period start, and
  period end.
- Material revisions require supporting narrative review.

## Alternatives considered

Always using original filings can mismatch the current accounting basis.
Always using the newest value hides publication context. Treating every change
as a restatement overstates what the evidence establishes.
