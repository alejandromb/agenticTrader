import json

import pytest
from pydantic import ValidationError

from agentic_trading.briefing import Entry, OpportunityScan, render_briefing


def test_empty_briefing(tmp_path):
    assert b"No briefing saved" in render_briefing(tmp_path / "missing.json")


@pytest.mark.parametrize(
    "url",
    ["javascript:alert(1)", "file:///etc/passwd", "https://user:pass@example.com"],
)
def test_unsafe_source_rejected(url):
    with pytest.raises(ValidationError):
        Entry(title="x", detail="x", source=url)


def test_briefing_escapes_private_content_and_labels_old_snapshot(tmp_path):
    path = tmp_path / "latest.json"
    path.write_text(
        json.dumps(
            dict(
                updated_at="2020-01-01T00:00:00Z",
                headline="<script>alert(1)</script>",
                summary="saved",
                metrics=[],
                decisions=[],
                news=[],
                work=[],
                limitations=["<img src=x onerror=alert(1)>"],
            )
        )
    )
    result = render_briefing(path).decode()
    assert "<script>" not in result
    assert "&lt;script&gt;" in result
    assert "Earlier briefing" in result
    assert "No background monitoring" in result
    assert "Opportunity scan: not run" in result


@pytest.mark.parametrize(
    "changes",
    [
        {"reviewed": ["V"]},
        {"status": "completed", "universe": ["V"]},
        {
            "status": "completed",
            "universe": ["V", "DE"],
            "reviewed": ["V"],
            "scanned_at": "2026-09-10T12:00:00Z",
        },
        {
            "status": "partial",
            "universe": ["V"],
            "reviewed": ["DE"],
            "scanned_at": "2026-09-10T12:00:00Z",
        },
        {"universe": ["V", "V"]},
    ],
)
def test_scan_rejects_misleading_coverage(changes):
    with pytest.raises(ValidationError):
        OpportunityScan(**changes)


def test_scan_rendering_and_escaping(tmp_path):
    path = tmp_path / "briefing.json"
    path.write_text(
        json.dumps(
            dict(
                updated_at="2026-09-10T12:00:00Z",
                headline="test",
                summary="test",
                metrics=[],
                decisions=[],
                news=[],
                work=[],
                limitations=[],
                portfolio_review="<script>bad</script>",
                opportunity_scan=dict(
                    status="completed",
                    scanned_at="2026-09-10T12:00:00Z",
                    universe=["V"],
                    reviewed=["V"],
                    method="Manual pilot",
                    candidates=[dict(title="V", detail="<img src=x>")],
                    limitations=["<script>gap</script>"],
                ),
            )
        )
    )
    result = render_briefing(path).decode()
    assert "completed · 1/1 declared names" in result
    assert "Not a market-wide search" in result
    assert "<script>" not in result
    assert "&lt;img src=x&gt;" in result
