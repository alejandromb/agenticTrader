"""Deterministic extraction of capital-allocation statements from SEC filings."""

from __future__ import annotations

import re
from html.parser import HTMLParser

_CAPEX = re.compile(r"\bcapital expenditures?\b", re.IGNORECASE)
_PURPOSE = re.compile(
    r"\b(support|focus|strategy|initiative|technology|automation|"
    r"supply chain|store|club|capacity|growth|infrastructure|omnichannel)\w*\b",
    re.IGNORECASE,
)
_STRONG_PURPOSE = re.compile(
    r"\b(to support|focused on|focus on|strategy includes|primarily related to|"
    r"allocated? to)\b",
    re.IGNORECASE,
)
_BOILERPLATE = re.compile(
    r"\b(risk|failure|expectations|stock price|market price|adversely affect|"
    r"expected to be financed)\b",
    re.IGNORECASE,
)
_CAPITAL_DETAIL = re.compile(
    r"\b(supply chain|remodel\w*|new stores?|new clubs?|expansion|relocation|"
    r"technology|customer-facing|international|total capital expenditures?)\b",
    re.IGNORECASE,
)
_SPACE = re.compile(r"\s+")


class _BlockTextParser(HTMLParser):
    _BLOCKS = {
        "div",
        "li",
        "p",
        "section",
        "td",
        "th",
        "tr",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self._BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


class _TableRowParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.current: list[str] | None = None
        self.rows: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.current = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "tr" and self.current is not None:
            row = _SPACE.sub(" ", " ".join(self.current)).strip()
            if row:
                self.rows.append(row)
            self.current = None

    def handle_data(self, data: str) -> None:
        if self.current is not None:
            value = data.strip()
            if value:
                self.current.append(value)


def extract_capital_allocation_statements(
    filing_html: bytes, *, limit: int = 5
) -> tuple[str, ...]:
    """Return bounded filing passages that state a purpose for capital spending."""
    parser = _BlockTextParser()
    parser.feed(filing_html.decode("utf-8", errors="replace"))
    candidates: list[tuple[int, int, str]] = []
    seen: set[str] = set()
    for raw_block in "".join(parser.parts).splitlines():
        block = _SPACE.sub(" ", raw_block).strip()
        if not 40 <= len(block) <= 1200:
            continue
        if not (_CAPEX.search(block) and _PURPOSE.search(block)):
            continue
        score = 2 * len(_STRONG_PURPOSE.findall(block))
        score += min(len(_PURPOSE.findall(block)), 3)
        score -= 2 * len(_BOILERPLATE.findall(block))
        if score < 3:
            continue
        key = block.casefold()
        if key in seen:
            continue
        seen.add(key)
        candidates.append((score, len(candidates), block))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return tuple(block for _, _, block in candidates[:limit])


def extract_capital_allocation_table_details(
    filing_html: bytes, *, limit: int = 12
) -> tuple[str, ...]:
    """Extract quantified capital-allocation rows from filing tables."""
    parser = _TableRowParser()
    parser.feed(filing_html.decode("utf-8", errors="replace"))
    total_indices = [
        index
        for index, row in enumerate(parser.rows)
        if re.search(r"\btotal capital expenditures?\b", row, re.IGNORECASE)
    ]
    rows = parser.rows
    if total_indices:
        selected: list[str] = []
        for index in total_indices:
            window = parser.rows[max(0, index - 12) : index + 1]
            context = "; ".join(
                row
                for row in window
                if re.search(
                    r"amounts in|allocation of capital expenditures",
                    row,
                    re.IGNORECASE,
                )
            )
            selected.extend(f"{context}; {row}" if context else row for row in window)
        rows = selected
    details: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not (20 <= len(row) <= 700):
            continue
        if not (_CAPITAL_DETAIL.search(row) and re.search(r"\d", row)):
            continue
        key = row.casefold()
        if key in seen:
            continue
        seen.add(key)
        details.append(row)
        if len(details) == limit:
            break
    return tuple(details)
