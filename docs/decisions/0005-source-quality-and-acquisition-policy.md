# ADR-0005: Adopt a primary-source-first evidence policy

- Status: Accepted
- Date: 2026-06-30

## Context

Research quality depends on the provenance, timeliness, and interpretation of
source material. Search snippets, unattributed summaries, and stale pages can
produce plausible but unsupported claims. At the same time, requiring only
company or regulatory materials would exclude useful independent context and
could reproduce management's framing without challenge.

## Decision

Version one will use a primary-source-first evidence policy.

Sources are divided into three tiers:

1. **Authoritative primary sources:** SEC filings, official government data,
   exchange notices, court or regulator publications, and audited company
   reports.
2. **Issuer primary sources:** investor-relations materials, earnings-call
   transcripts published by the issuer, and official company announcements.
3. **Independent secondary sources:** reputable news, market-data, and industry
   research used for context, corroboration, or competing interpretations.

Material financial and legal facts must use Tier 1 evidence when available.
Issuer claims that are not independently established must remain attributed to
the issuer. Tier 3 sources cannot override a more authoritative source without
recording and explaining the conflict.

Search results, snippets, social posts, anonymous commentary, and model memory
may help discover sources but are not admissible as final evidence.

Every captured evidence record must include retrieval time, canonical URL,
publisher, source type, precise locator, normalized support, and a stable source
identifier when one exists. A content hash should be recorded when source bytes
are lawfully captured. Version one stores evidence metadata and minimal support,
not unrestricted copies of copyrighted source documents.

The memo's `as_of` time is a hard information boundary. Evidence published
after that time is prohibited from the original memo and may only appear in a
separately identified review.

## Consequences

- Financial claims are grounded in filings and official data where possible.
- Independent context remains available but carries clear provenance.
- Acquisition code must preserve timestamps and stable identifiers.
- Some useful sources may be excluded because they cannot be cited reliably or
  retained lawfully.
- Conflicting evidence becomes visible rather than silently reconciled.

## Alternatives considered

### Accept any publicly accessible webpage

Rejected because accessibility does not establish authority, durability, or
evidentiary quality.

### Use primary sources only

Rejected because primary sources may omit independent context and naturally
reflect the publisher's interests.

### Archive every complete source document

Rejected as a default because licensing, copyright, storage, and deletion
requirements vary. Source-specific capture rules can be added later.
