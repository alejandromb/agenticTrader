"""Dashboard facade that delegates every operation to accepted domain services."""

from __future__ import annotations

import json
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from agentic_trading.backtesting import SqliteBacktester
from agentic_trading.market_data import SqlitePriceDatasetRepository
from agentic_trading.monitoring import SqliteDecisionMonitoring
from agentic_trading.portfolio_analytics import SqlitePortfolioAnalyzer
from agentic_trading.research_reviews import SqliteResearchReviewRepository
from agentic_trading.screener import ScreenFilters, SqliteResearchScreener


class DashboardWorkspaceService:
    def __init__(self, database_path: Path, artifact_root: Path) -> None:
        self._prices = SqlitePriceDatasetRepository(database_path, artifact_root)
        self._screens = SqliteResearchScreener(database_path)
        self._portfolios = SqlitePortfolioAnalyzer(database_path, artifact_root)
        self._backtests = SqliteBacktester(database_path, artifact_root)
        self._monitoring = SqliteDecisionMonitoring(database_path, artifact_root)
        self._reviews = SqliteResearchReviewRepository(database_path)

    def snapshot(self) -> dict[str, Any]:
        return {
            "datasets": [asdict(item) for item in self._prices.list_datasets()],
            "monitors": [
                _monitor_payload(item) for item in self._monitoring.list_monitors()
            ],
            "alerts": [asdict(item) for item in self._monitoring.list_alerts()],
            "reviews": [
                {
                    **_review_payload(item),
                    "human_outcome": (
                        asdict(outcome)
                        if (outcome := self._reviews.outcome_for_review(item.review_id))
                        else None
                    ),
                }
                for item in self._reviews.list_reviews()
            ],
        }

    def import_prices(
        self, payload: bytes, *, source: str, adjustment_note: str
    ) -> dict[str, Any]:
        return asdict(
            self._prices.import_bytes(
                payload, source=source, adjustment_note=adjustment_note
            )
        )

    def screen(self, payload: dict[str, Any]) -> dict[str, Any]:
        artifact = self._screens.screen(
            as_of=_required_string(payload, "as_of"),
            filters=ScreenFilters(
                min_revenue_growth=_optional_decimal(payload, "min_revenue_growth"),
                min_operating_margin=_optional_decimal(payload, "min_operating_margin"),
                min_net_margin=_optional_decimal(payload, "min_net_margin"),
                min_current_ratio=_optional_decimal(payload, "min_current_ratio"),
                min_free_cash_flow=_optional_decimal(payload, "min_free_cash_flow"),
            ),
        )
        return {
            "screen_id": artifact.screen_id,
            "as_of": artifact.as_of,
            "filters": {
                key: str(value) if value is not None else None
                for key, value in asdict(artifact.filters).items()
            },
            "results": [asdict(item) for item in artifact.results],
        }

    def analyze_portfolio(
        self, payload: bytes, *, dataset_id: str, benchmark: str, as_of: str
    ) -> dict[str, Any]:
        artifact = self._portfolios.analyze_bytes(
            payload,
            dataset_id=dataset_id,
            benchmark=benchmark,
            as_of=as_of,
        )
        return {
            "analysis_id": artifact.analysis_id,
            "dataset_id": artifact.dataset_id,
            "as_of": artifact.as_of,
            "valuation_date": artifact.valuation_date,
            "benchmark": artifact.benchmark,
            "results": artifact.results,
        }

    def backtest(self, payload: dict[str, Any]) -> dict[str, Any]:
        artifact = self._backtests.run(
            _required_string(payload, "dataset_id"),
            ticker=_required_string(payload, "ticker"),
            benchmark=_required_string(payload, "benchmark"),
            short_window=_required_int(payload, "short_window"),
            long_window=_required_int(payload, "long_window"),
            initial_cash=_required_decimal(payload, "initial_cash"),
            transaction_cost_bps=_required_decimal(payload, "transaction_cost_bps"),
        )
        return asdict(artifact)

    def create_monitor(
        self, *, run_id: str, name: str, rules: list[dict[str, Any]]
    ) -> dict[str, Any]:
        monitor = self._monitoring.create_monitor_bytes(
            run_id=run_id,
            name=name,
            payload=json.dumps(rules, separators=(",", ":")).encode(),
        )
        return _monitor_payload(monitor)

    def evaluate_monitor(
        self, monitor_id: str, *, dataset_id: str, as_of: str
    ) -> dict[str, Any]:
        return asdict(
            self._monitoring.evaluate(monitor_id, dataset_id=dataset_id, as_of=as_of)
        )

    def acknowledge_alert(self, alert_id: str, *, note: str) -> dict[str, Any]:
        return asdict(self._monitoring.acknowledge(alert_id, note=note))

    def compare_research(self, baseline: str, current: str) -> dict[str, Any]:
        return _review_payload(self._reviews.compare(baseline, current))

    def review(self, review_id: str) -> dict[str, Any]:
        review = self._reviews.get(review_id)
        outcome = self._reviews.outcome_for_review(review_id)
        return {
            **_review_payload(review),
            "human_outcome": asdict(outcome) if outcome else None,
        }

    def record_review_outcome(
        self, review_id: str, *, outcome: str, rationale: str
    ) -> dict[str, Any]:
        return asdict(
            self._reviews.record_outcome(
                review_id, outcome=outcome, rationale=rationale
            )
        )


def _monitor_payload(monitor) -> dict[str, Any]:
    return {
        "monitor_id": monitor.monitor_id,
        "run_id": monitor.run_id,
        "name": monitor.name,
        "rules_sha256": monitor.rules_sha256,
        "rules": [
            {
                "rule_id": rule.rule_id,
                "type": rule.type,
                "ticker": rule.ticker,
                "threshold": str(rule.threshold),
            }
            for rule in monitor.rules
        ],
        "created_at": monitor.created_at,
    }


def _review_payload(review) -> dict[str, Any]:
    return {
        "review_id": review.review_id,
        "baseline_run_id": review.baseline_run_id,
        "current_run_id": review.current_run_id,
        "baseline_memo_id": review.baseline_memo_id,
        "current_memo_id": review.current_memo_id,
        "ticker": review.ticker,
        "content": review.content,
        "created_at": review.created_at,
    }


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a nonempty string")
    return value.strip()


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{key} must be an integer") from error


def _required_decimal(payload: dict[str, Any], key: str) -> Decimal:
    value = payload.get(key)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise ValueError(f"{key} must be a decimal") from error


def _optional_decimal(payload: dict[str, Any], key: str) -> Decimal | None:
    value = payload.get(key)
    if value is None or value == "":
        return None
    return _required_decimal(payload, key)
