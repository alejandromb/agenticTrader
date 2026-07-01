"""Minimal, fair-access client for public SEC EDGAR data."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"


class SecClientError(RuntimeError):
    """Raised when an SEC response cannot be acquired or interpreted."""


@dataclass(frozen=True, slots=True)
class FilingMetadata:
    """Normalized metadata for one public EDGAR filing."""

    accession_number: str
    form: str
    filing_date: str
    report_date: str
    primary_document: str


@dataclass(frozen=True, slots=True)
class CompanyIdentity:
    cik: str
    ticker: str
    name: str


class SecClient:
    """Access public SEC submissions while enforcing identification and pacing."""

    def __init__(
        self,
        user_agent: str,
        *,
        minimum_interval: float = 0.2,
        opener: Callable[..., Any] = urlopen,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not user_agent.strip() or "example.com" in user_agent.lower():
            raise ValueError("Use a real identifying SEC User-Agent")
        if minimum_interval < 0.1:
            raise ValueError("SEC requests must be limited to 10 per second or less")
        self._user_agent = user_agent
        self._minimum_interval = minimum_interval
        self._opener = opener
        self._clock = clock
        self._sleep = sleep
        self._last_request_at: float | None = None

    def get_submissions(self, cik: str | int) -> dict[str, Any]:
        """Return the SEC submissions object for a company CIK."""
        normalized_cik = normalize_cik(cik)
        return self._get_json(SUBMISSIONS_URL.format(cik=normalized_cik))

    def get_company_facts(self, cik: str | int) -> dict[str, Any]:
        """Return standardized XBRL facts disclosed by a company."""
        normalized_cik = normalize_cik(cik)
        return self._get_json(COMPANY_FACTS_URL.format(cik=normalized_cik))

    def resolve_ticker(self, ticker: str) -> CompanyIdentity:
        """Resolve a U.S. public-company ticker using the SEC mapping."""
        normalized_ticker = ticker.strip().upper()
        mapping = self._get_json(COMPANY_TICKERS_URL)
        for entry in mapping.values():
            if str(entry.get("ticker", "")).upper() == normalized_ticker:
                return CompanyIdentity(
                    cik=normalize_cik(entry["cik_str"]),
                    ticker=normalized_ticker,
                    name=entry["title"],
                )
        raise SecClientError(f"Ticker not found in SEC mapping: {normalized_ticker}")

    def list_recent_filings(
        self, submissions: Mapping[str, Any], *, form: str | None = None
    ) -> list[FilingMetadata]:
        """Normalize the compact recent-filings table in a submissions response."""
        recent = submissions.get("filings", {}).get("recent", {})
        required = (
            "accessionNumber",
            "form",
            "filingDate",
            "reportDate",
            "primaryDocument",
        )
        if not all(isinstance(recent.get(key), list) for key in required):
            raise SecClientError("SEC submissions response lacks recent filing columns")

        lengths = {len(recent[key]) for key in required}
        if len(lengths) != 1:
            raise SecClientError("SEC recent filing columns have inconsistent lengths")

        filings = [
            FilingMetadata(
                accession_number=accession,
                form=filing_form,
                filing_date=filing_date,
                report_date=report_date,
                primary_document=document,
            )
            for accession, filing_form, filing_date, report_date, document in zip(
                *(recent[key] for key in required), strict=True
            )
        ]
        if form is None:
            return filings
        return [filing for filing in filings if filing.form == form]

    def filing_url(self, cik: str | int, filing: FilingMetadata) -> str:
        """Build the canonical SEC Archives URL for a filing's primary document."""
        cik_without_zeroes = str(int(normalize_cik(cik)))
        accession_without_hyphens = filing.accession_number.replace("-", "")
        return ARCHIVES_URL.format(
            cik=cik_without_zeroes,
            accession=accession_without_hyphens,
            document=filing.primary_document,
        )

    def get_filing_document(self, cik: str | int, filing: FilingMetadata) -> bytes:
        """Retrieve a primary filing document from the SEC Archives."""
        return self._get_bytes(
            self.filing_url(cik, filing), accept="text/html,application/xhtml+xml"
        )

    def _get_json(self, url: str) -> dict[str, Any]:
        payload = self._get_bytes(url, accept="application/json")
        try:
            value = json.loads(payload)
        except (UnicodeDecodeError, ValueError) as error:
            raise SecClientError(f"SEC returned invalid JSON from {url}") from error
        if not isinstance(value, dict):
            raise SecClientError("Expected the SEC endpoint to return a JSON object")
        return value

    def _get_bytes(self, url: str, *, accept: str) -> bytes:
        self._pace_request()
        request = Request(
            url,
            headers={
                "Accept": accept,
                "User-Agent": self._user_agent,
            },
        )
        try:
            with self._opener(request, timeout=30) as response:
                payload = response.read()
        except OSError as error:
            raise SecClientError(f"Unable to retrieve SEC data from {url}") from error
        return payload

    def _pace_request(self) -> None:
        now = self._clock()
        if self._last_request_at is not None:
            wait = self._minimum_interval - (now - self._last_request_at)
            if wait > 0:
                self._sleep(wait)
                now = self._clock()
        self._last_request_at = now


def normalize_cik(cik: str | int) -> str:
    """Return a zero-padded 10-digit CIK."""
    value = str(cik).strip()
    if not value.isdigit() or len(value) > 10:
        raise ValueError(f"Invalid CIK: {cik!r}")
    return value.zfill(10)


def iter_filings(
    client: SecClient, cik: str | int, *, form: str | None = None
) -> Iterator[FilingMetadata]:
    """Yield recent filings for a CIK, optionally filtered by exact form type."""
    yield from client.list_recent_filings(client.get_submissions(cik), form=form)
