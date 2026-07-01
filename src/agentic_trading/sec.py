"""Minimal, fair-access client for public SEC EDGAR data."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any
from urllib.request import Request, urlopen

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
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

    def _get_json(self, url: str) -> dict[str, Any]:
        self._pace_request()
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": self._user_agent,
            },
        )
        try:
            with self._opener(request, timeout=30) as response:
                payload = json.load(response)
        except (OSError, ValueError) as error:
            raise SecClientError(f"Unable to retrieve SEC data from {url}") from error
        if not isinstance(payload, dict):
            raise SecClientError("Expected the SEC endpoint to return a JSON object")
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
