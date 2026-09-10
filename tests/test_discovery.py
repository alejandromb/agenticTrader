import json
from datetime import date

import pytest

from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.discovery import normalize_calendar, save_discovery


def event(**changes):
    row = dict(
        symbol="ABC",
        year=2026,
        quarter=3,
        eps={"actual": None},
        report={"date": "2026-09-10", "timing": "pm", "verified": False},
    )
    return row | changes


def run(rows):
    return normalize_calendar(rows, start=date(2026, 9, 10), days=14)


def test_duplicate_not_double_counted():
    result = run([event(), event()])
    assert len(result["queue"]) == 1
    assert len(result["duplicates"]) == 1
    assert result["queue"][0]["date_status"] == "tentative"


def test_conflicting_records_quarantined_not_cherry_picked():
    result = run([event(), event(eps={"actual": "1.0"})])
    assert not result["queue"]
    assert len(result["quarantined"]) == 2


@pytest.mark.parametrize(
    "row",
    [
        None,
        {},
        event(year=2023),
        event(quarter=5),
        event(report={"date": "2026-10-01"}),
        event(symbol=""),
        event(report={"date": "2026-09-10", "verified": "false"}),
    ],
)
def test_bad_rows_visible(row):
    result = run([row])
    assert len(result["quarantined"]) == 1
    assert not result["queue"]


def test_actual_zero_is_reported_not_missing():
    assert run([event(eps={"actual": "0"})])["queue"][0]["stage"] == "verify_results"


def test_empty_not_failure():
    assert run([])["input_count"] == 0


@pytest.mark.parametrize("days", [0, -1, 32])
def test_invalid_window(days):
    with pytest.raises(ValueError):
        normalize_calendar([], start=date(2026, 9, 10), days=days)


def test_archive_repeatability_and_provenance(tmp_path):
    payload = dict(
        retrieved_at="2026-09-10T12:00:00Z",
        start_date="2026-09-10",
        days=14,
        calendar_rows=[event()],
        provider="test",
    )
    digest = save_discovery(payload, tmp_path)
    assert save_discovery(payload, tmp_path) == digest
    data = json.loads(LocalArtifactStore(tmp_path).get(digest))
    assert data["input"] == payload
    assert data["result"]["queue"][0]["source_row"] == 0
