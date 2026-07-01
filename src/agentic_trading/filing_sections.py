"""Deterministic extraction of bounded business and risk evidence from 10-Ks."""

from __future__ import annotations

import re
from dataclasses import dataclass

from agentic_trading.filing_narrative import extract_filing_blocks

_BUSINESS = re.compile(
    r"\b(segment|business|customer|member|product|service|strategy|ecommerce|"
    r"omnichannel|market|distribution|operation)\w*\b",
    re.IGNORECASE,
)
_RISK = re.compile(
    r"\b(risk|may|could|uncertain|adverse|failure|depend|competition|"
    r"regulation|cybersecurity|supply chain)\w*\b",
    re.IGNORECASE,
)
_BOILERPLATE = re.compile(
    r"\b(table of contents|incorporated by reference|see item|page \d+)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class FilingSectionEvidence:
    business: tuple[str, ...]
    risks: tuple[str, ...]


def extract_business_and_risk_evidence(
    filing_html: bytes, *, business_limit: int = 12, risk_limit: int = 16
) -> FilingSectionEvidence:
    """Extract representative Item 1 and Item 1A paragraphs from a Form 10-K."""
    blocks = extract_filing_blocks(filing_html)
    business = _section(blocks, "ITEM 1.", "ITEM 1A.")
    risks = _section(blocks, "ITEM 1A.", "ITEM 1B.")
    return FilingSectionEvidence(
        business=_rank(business, _BUSINESS, business_limit),
        risks=_rank(risks, _RISK, risk_limit),
    )


def _section(blocks: tuple[str, ...], start: str, end: str) -> tuple[str, ...]:
    try:
        start_index = blocks.index(start)
        end_index = blocks.index(end, start_index + 1)
    except ValueError:
        return ()
    return blocks[start_index + 1 : end_index]


def _rank(
    blocks: tuple[str, ...], pattern: re.Pattern[str], limit: int
) -> tuple[str, ...]:
    candidates: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    for index, block in enumerate(blocks):
        if not 80 <= len(block) <= 2000 or _BOILERPLATE.search(block):
            continue
        matches = pattern.findall(block)
        if not matches:
            continue
        key = block.casefold()
        if key in seen:
            continue
        seen.add(key)
        candidates.append((min(len(matches), 8), index, block))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    selected = sorted(candidates[:limit], key=lambda item: item[1])
    return tuple(block for _, _, block in selected)
