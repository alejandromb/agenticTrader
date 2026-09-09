"""Escaped, read-only rendering of private daily briefing files."""

from datetime import UTC, datetime
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


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
        body = (
            f'<p class="eyebrow">DAILY BRIEFING / {stamp:%d %B %Y}</p>'
            f'<h1>{escape(b.headline)}</h1><p class="lead">{escape(b.summary)}</p>'
            f'<p class="freshness">{freshness} · Updated {stamp:%H:%M UTC}</p>'
            f'<section class="metrics">{_entries(b.metrics)}</section>'
            '<div class="columns"><section><h2>01 / Decisions today</h2>'
            f"{_entries(b.decisions)}</section>"
            "<section><h2>02 / Events &amp; evidence</h2>"
            f"{_entries(b.news)}</section></div>"
            '<section><h2>03 / Workbench</h2><div class="work">'
            f"{_entries(b.work)}</div></section>"
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
