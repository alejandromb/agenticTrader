"""Escaped, read-only rendering of private daily briefing files."""

from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str
    detail: str
    source: str | None = None

    @field_validator("source")
    @classmethod
    def safe_source(cls, value):
        if value is not None:
            url = urlparse(value)
            if (
                url.scheme != "https"
                or not url.hostname
                or url.username
                or url.password
            ):
                raise ValueError("Source must be HTTPS without credentials")
        return value


class OpportunityScan(BaseModel):
    """Coverage declaration, not an automated screener or trading signal."""

    model_config = ConfigDict(extra="forbid")
    status: Literal["not_run", "partial", "completed"] = "not_run"
    scanned_at: AwareDatetime | None = None
    universe: list[str] = Field(default_factory=list)
    reviewed: list[str] = Field(default_factory=list)
    method: str = "No opportunity scan recorded."
    candidates: list[Entry] = Field(default_factory=list, max_length=4)
    limitations: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def consistent_coverage(self):
        if len(set(self.universe)) != len(self.universe) or len(
            set(self.reviewed)
        ) != len(self.reviewed):
            raise ValueError("Duplicate coverage symbols")
        if not set(self.reviewed).issubset(self.universe):
            raise ValueError("Reviewed symbols must belong to the declared universe")
        if self.status == "not_run":
            if self.reviewed or self.candidates or self.scanned_at:
                raise ValueError("Unrun scan cannot contain results")
        elif not self.scanned_at or not self.universe:
            raise ValueError("Scan requires a timestamp and explicit universe")
        if self.status == "completed" and set(self.reviewed) != set(self.universe):
            raise ValueError("Completed means every declared symbol was reviewed")
        return self


class Briefing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    updated_at: AwareDatetime
    headline: str
    summary: str
    metrics: list[Entry] = Field(max_length=4)
    decisions: list[Entry]
    news: list[Entry]
    work: list[Entry]
    limitations: list[str]
    portfolio_review: str = "Portfolio review coverage not recorded."
    opportunity_scan: OpportunityScan = Field(default_factory=OpportunityScan)


def _entries(items):
    output = []
    for item in items:
        link = (
            f'<a href="{escape(item.source, quote=True)}" target="_blank" '
            'rel="noopener noreferrer">Source ↗</a>'
            if item.source
            else ""
        )
        output.append(
            f"<article><h3>{escape(item.title)}</h3>"
            f"<p>{escape(item.detail)}</p>{link}</article>"
        )
    return "".join(output)


def render_briefing(path: Path) -> bytes:
    if not path.exists():
        body = "<h1>No briefing saved yet</h1><p>Ask for a daily briefing to begin.</p>"
    else:
        b = Briefing.model_validate_json(path.read_text())
        stamp = b.updated_at.astimezone(UTC)
        freshness = (
            "Earlier briefing — request an update"
            if stamp.date() != datetime.now(UTC).date()
            else "Saved snapshot · not a live feed"
        )
        scan = b.opportunity_scan
        scan_time = (
            f" · As of {scan.scanned_at.astimezone(UTC):%d %b %Y %H:%M UTC}"
            if scan.scanned_at
            else ""
        )
        coverage = (
            "<section><h2>Review coverage</h2>"
            f"<p>Portfolio: {escape(b.portfolio_review)}</p>"
            f"<p>Opportunity scan: {escape(scan.status.replace('_', ' '))}"
            f" · {len(scan.reviewed)}/{len(scan.universe)} declared names"
            f"{scan_time}</p>"
            f"<p>{escape(scan.method)}</p>"
            f"<p>Universe: {escape(', '.join(scan.universe)) or 'Not declared'}. "
            "Not a market-wide search or a completed investment thesis.</p></section>"
        )
        body = (
            f'<p class="eyebrow">DAILY BRIEFING / {stamp:%d %B %Y}</p>'
            f'<h1>{escape(b.headline)}</h1><p class="lead">{escape(b.summary)}</p>'
            f'<p class="freshness">{freshness} · Updated {stamp:%H:%M UTC}</p>'
            f'<section class="metrics">{_entries(b.metrics)}</section>'
            + coverage
            + '<div class="columns"><section><h2>01 / Decisions today</h2>'
            f"{_entries(b.decisions)}</section>"
            "<section><h2>02 / Events &amp; evidence</h2>"
            f"{_entries(b.news)}</section></div>"
            '<section><h2>03 / Workbench</h2><div class="work">'
            f"{_entries(b.work)}</div></section>"
            "<section><h2>04 / Opportunity radar · research leads</h2>"
            + (_entries(scan.candidates) or "<p>No candidate results recorded.</p>")
            + "".join(f"<p>{escape(line)}</p>" for line in scan.limitations)
            + "</section>"
            "<details><summary>Known limitations &amp; safety boundaries</summary><ul>"
            + "".join(f"<li>{escape(line)}</li>" for line in b.limitations)
            + "</ul></details>"
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Daily briefing · Agentic Trading</title>"
        '<link rel="stylesheet" href="/briefing.css"></head><body><main>'
        '<nav><a class="brand" href="/briefing">AT · Agentic Trading</a>'
        '<a href="/">Research workspace ↗</a></nav>'
        + body
        + "<footer>Read the briefing. Discuss in chat. Decide deliberately."
        "<br>No trading controls · No background monitoring · Local only</footer>"
        "</main></body></html>"
    ).encode()
