from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

ASSETS = Path(__file__).parents[1] / "src/agentic_trading/dashboard_assets"


class DashboardStructure(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, dict[str, str | None]]] = []
        self.forms_in_details: set[str] = set()
        self.primary_workspaces: list[str] = []
        self.question_summaries = 0

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        attributes = dict(attrs)
        ancestors = tuple(self.stack)
        if (
            tag == "form"
            and any(item[0] == "details" for item in ancestors)
            and (form_id := attributes.get("id"))
        ):
            self.forms_in_details.add(form_id)
        if (
            tag == "button"
            and (workspace := attributes.get("data-workspace"))
            and not any(item[0] == "details" for item in ancestors)
        ):
            self.primary_workspaces.append(workspace)
        if tag == "summary" and any(
            item[1].get("class") == "tool-disclosure" for item in ancestors
        ):
            self.question_summaries += 1
        if tag not in {"input", "meta", "link", "br", "hr"}:
            self.stack.append((tag, attributes))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                return


def test_dashboard_uses_progressive_disclosure_without_losing_workflows() -> None:
    page = (ASSETS / "index.html").read_text()
    structure = DashboardStructure()
    structure.feed(page)

    assert structure.primary_workspaces == ["research", "reviews"]
    assert structure.forms_in_details == {
        "price-import-form",
        "screen-form",
        "portfolio-form",
        "backtest-form",
        "monitor-form",
        "monitor-evaluate-form",
        "review-form",
        "quality-evaluation-form",
    }
    assert structure.question_summaries == 8
    assert page.index('id="decision-panel"') < page.index(
        'class="evidence-disclosure"'
    )
    assert "Known limitations" in page
    assert "Explore the full decision record" in page
    assert "quant-guidance" in page
    assert "monitoring-guidance" in page
    assert "Start by importing a price dataset" in (
        ASSETS / "app.js"
    ).read_text()
    assert "Monitoring needs a completed Watch decision" in (
        ASSETS / "app.js"
    ).read_text()


def test_future_visualization_backlog_is_not_added_to_dashboard() -> None:
    page = (ASSETS / "index.html").read_text().lower()

    for deferred_feature in (
        "portfolio heatmap",
        "sector exposure",
        "correlation matrix",
        "factor exposure",
        "decision quality metrics",
    ):
        assert deferred_feature not in page
