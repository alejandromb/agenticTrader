from __future__ import annotations

import io
import json
from typing import Any

import pytest

from agentic_trading.sec import (
    CompanyIdentity,
    FilingMetadata,
    SecClient,
    SecClientError,
    normalize_cik,
)


class Response(io.BytesIO):
    def __enter__(self) -> Response:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


def test_normalize_cik() -> None:
    assert normalize_cik(320193) == "0000320193"
    assert normalize_cik("0000320193") == "0000320193"


def test_invalid_cik_is_rejected() -> None:
    with pytest.raises(ValueError, match="Invalid CIK"):
        normalize_cik("AAPL")


def test_client_identifies_itself_and_reads_submissions() -> None:
    captured_request = None

    def opener(request: Any, *, timeout: int) -> Response:
        nonlocal captured_request
        captured_request = request
        assert timeout == 30
        return Response(json.dumps({"cik": "320193"}).encode())

    client = SecClient("AgenticTrading/0.1 owner@domain.test", opener=opener)

    assert client.get_submissions(320193) == {"cik": "320193"}
    assert captured_request.full_url.endswith("CIK0000320193.json")
    assert captured_request.get_header("User-agent").startswith("AgenticTrading")


def test_client_reads_company_facts() -> None:
    captured_request = None

    def opener(request: Any, *, timeout: int) -> Response:
        nonlocal captured_request
        captured_request = request
        assert timeout == 30
        return Response(json.dumps({"facts": {}}).encode())

    client = SecClient("AgenticTrading/0.1 owner@domain.test", opener=opener)

    assert client.get_company_facts(320193) == {"facts": {}}
    assert captured_request.full_url.endswith("companyfacts/CIK0000320193.json")


def test_resolve_ticker() -> None:
    def opener(request: Any, *, timeout: int) -> Response:
        assert timeout == 30
        assert request.full_url.endswith("company_tickers.json")
        return Response(
            json.dumps(
                {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}
            ).encode()
        )

    client = SecClient("AgenticTrading/0.1 owner@domain.test", opener=opener)

    assert client.resolve_ticker("aapl") == CompanyIdentity(
        cik="0000320193", ticker="AAPL", name="Apple Inc."
    )


def test_client_retrieves_primary_filing_document() -> None:
    captured_request = None

    def opener(request: Any, *, timeout: int) -> Response:
        nonlocal captured_request
        captured_request = request
        assert timeout == 30
        return Response(b"<html>filing</html>")

    client = SecClient("AgenticTrading/0.1 owner@domain.test", opener=opener)
    filing = FilingMetadata(
        accession_number="0000320193-25-000079",
        form="10-K",
        filing_date="2025-10-31",
        report_date="2025-09-27",
        primary_document="aapl-20250927.htm",
    )

    assert client.get_filing_document(320193, filing) == b"<html>filing</html>"
    assert captured_request.get_header("Accept").startswith("text/html")


def test_recent_filings_are_normalized_and_filtered() -> None:
    client = SecClient("AgenticTrading/0.1 owner@domain.test")
    submissions = {
        "filings": {
            "recent": {
                "accessionNumber": ["0000320193-25-000079", "0000320193-25-000057"],
                "form": ["10-K", "10-Q"],
                "filingDate": ["2025-10-31", "2025-08-01"],
                "reportDate": ["2025-09-27", "2025-06-28"],
                "primaryDocument": ["aapl-20250927.htm", "aapl-20250628.htm"],
            }
        }
    }

    filings = client.list_recent_filings(submissions, form="10-K")

    assert filings == [
        FilingMetadata(
            accession_number="0000320193-25-000079",
            form="10-K",
            filing_date="2025-10-31",
            report_date="2025-09-27",
            primary_document="aapl-20250927.htm",
        )
    ]
    assert client.filing_url(320193, filings[0]) == (
        "https://www.sec.gov/Archives/edgar/data/320193/"
        "000032019325000079/aapl-20250927.htm"
    )


def test_malformed_recent_filing_columns_are_rejected() -> None:
    client = SecClient("AgenticTrading/0.1 owner@domain.test")

    with pytest.raises(SecClientError, match="lacks recent filing columns"):
        client.list_recent_filings({"filings": {"recent": {}}})


def test_rate_limit_below_sec_maximum_is_enforced() -> None:
    with pytest.raises(ValueError, match="10 per second"):
        SecClient("AgenticTrading/0.1 owner@domain.test", minimum_interval=0.09)
