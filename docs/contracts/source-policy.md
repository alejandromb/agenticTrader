# Version-One Source Policy

## Accepted sources

| Tier | Source examples | Permitted use |
| --- | --- | --- |
| 1 | SEC EDGAR, Federal Reserve, BLS, BEA, regulators, courts, exchanges | Authoritative facts and legal or regulatory status |
| 2 | Company filings mirrored on investor relations, earnings releases, issuer transcripts, official announcements | Company-reported results, strategy, and attributed management claims |
| 3 | Licensed market data, reputable news, identified industry research | Market context, triangulation, and independent interpretation |

Tier describes authority for a particular claim, not universal source quality.
For example, a company is authoritative about the text of its announcement but
not necessarily about the likelihood that its strategy will succeed.

## Rejected as final evidence

- Search-result and AI-summary snippets
- Unsourced aggregations
- Anonymous social posts or forums
- Model recollection without a captured source
- Pages without an identifiable publisher and retrieval path
- Sources whose terms do not permit the intended access or retention

## Acquisition requirements

For every accepted source, capture:

- canonical URL and publisher;
- publication time when available;
- retrieval time;
- stable identifier such as SEC accession number when available;
- precise section, page, table, or data-series locator;
- normalized value or minimal supporting excerpt;
- content hash when source bytes are retained; and
- acquisition errors, access restrictions, or transformations.

Acquisition must respect source terms, copyright, robots policies, rate limits,
and applicable licenses. Credentials used for licensed sources are configuration
secrets and never part of evidence records.

## Conflict handling

Conflicting sources are retained as separate evidence records. The memo must:

1. identify the conflict;
2. rank the sources for the specific claim;
3. explain any selected interpretation; and
4. preserve uncertainty when the conflict cannot be resolved.

## Freshness

Freshness is claim-specific. Each later workflow must define a maximum age for
time-sensitive inputs such as prices, shares outstanding, analyst estimates, or
macroeconomic series. Annual-report facts remain tied to their reporting period
and must not be described as current without newer corroboration.
