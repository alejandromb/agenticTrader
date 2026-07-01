"""Deterministic monitoring of human-approved research follow-up criteria."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.database import create_sqlite_engine
from agentic_trading.market_data import SqlitePriceDatasetRepository
from agentic_trading.models import (
    AlertAcknowledgementModel,
    DecisionMonitorModel,
    HumanDispositionEventModel,
    MonitorAlertModel,
    MonitorEvaluationModel,
    ResearchRunModel,
)

SUPPORTED_RULES = {"price_above", "price_below", "drawdown_at_least"}
ELIGIBLE_DISPOSITIONS = {"watch", "consider_for_portfolio"}
_IDENTIFIER = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]{0,63}$")
_TICKER = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")


class MonitoringError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class MonitorRule:
    rule_id: str
    type: str
    ticker: str
    threshold: Decimal


@dataclass(frozen=True, slots=True)
class DecisionMonitor:
    monitor_id: str
    run_id: str
    name: str
    rules_sha256: str
    rules_storage_path: str
    rules: tuple[MonitorRule, ...]
    created_at: str


@dataclass(frozen=True, slots=True)
class MonitorEvaluation:
    evaluation_id: str
    monitor_id: str
    dataset_id: str
    dataset_sha256: str
    as_of: str
    results: tuple[dict, ...]
    created_at: str


@dataclass(frozen=True, slots=True)
class MonitorAlert:
    alert_id: str
    evaluation_id: str
    monitor_id: str
    rule_id: str
    evidence: dict
    status: str
    created_at: str


@dataclass(frozen=True, slots=True)
class AlertAcknowledgement:
    acknowledgement_id: str
    alert_id: str
    note: str
    actor: str
    acknowledged_at: str


class SqliteDecisionMonitoring:
    def __init__(self, database_path: Path, artifact_root: Path) -> None:
        self._prices = SqlitePriceDatasetRepository(database_path, artifact_root)
        self._artifacts = LocalArtifactStore(artifact_root)
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )

    def create_monitor(
        self, *, run_id: str, name: str, rules_path: Path
    ) -> DecisionMonitor:
        return self.create_monitor_bytes(
            run_id=run_id, name=name, payload=rules_path.read_bytes()
        )

    def create_monitor_bytes(
        self, *, run_id: str, name: str, payload: bytes
    ) -> DecisionMonitor:
        name = name.strip()
        if not name:
            raise MonitoringError("Monitor name is required")
        rules = _parse_rules(payload)
        with self._sessions() as session:
            run = session.get(ResearchRunModel, run_id)
            if run is None:
                raise MonitoringError(f"Research run not found: {run_id}")
            disposition = session.scalar(
                select(HumanDispositionEventModel).where(
                    HumanDispositionEventModel.run_id == run_id
                )
            )
            if run.state != "complete" or disposition is None:
                raise MonitoringError(
                    "Monitor requires a completed run with a human disposition"
                )
            if disposition.status not in ELIGIBLE_DISPOSITIONS:
                raise MonitoringError(
                    "Monitor requires watch or consider_for_portfolio disposition"
                )
        stored = self._artifacts.put(payload)
        model = DecisionMonitorModel(
            monitor_id=str(uuid4()),
            run_id=run_id,
            name=name,
            rules_sha256=stored.sha256,
            rules_storage_path=str(stored.path),
            rules_json=json.dumps([_rule_payload(rule) for rule in rules]),
            created_at=datetime.now(UTC).isoformat(),
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _monitor_from_model(model)

    def list_monitors(self) -> tuple[DecisionMonitor, ...]:
        with self._sessions() as session:
            models = session.scalars(
                select(DecisionMonitorModel).order_by(
                    DecisionMonitorModel.created_at.desc(),
                    DecisionMonitorModel.monitor_id,
                )
            ).all()
            return tuple(_monitor_from_model(model) for model in models)

    def get_monitor(self, monitor_id: str) -> DecisionMonitor:
        with self._sessions() as session:
            model = session.get(DecisionMonitorModel, monitor_id)
            if model is None:
                raise MonitoringError(f"Monitor not found: {monitor_id}")
            return _monitor_from_model(model)

    def evaluate(
        self, monitor_id: str, *, dataset_id: str, as_of: str
    ) -> MonitorEvaluation:
        boundary = _date(as_of)
        monitor = self.get_monitor(monitor_id)
        dataset = self._prices.get(dataset_id)
        with self._sessions() as session:
            existing = session.scalar(
                select(MonitorEvaluationModel).where(
                    MonitorEvaluationModel.monitor_id == monitor_id,
                    MonitorEvaluationModel.dataset_id == dataset_id,
                    MonitorEvaluationModel.as_of == boundary.isoformat(),
                )
            )
            if existing is not None:
                return _evaluation_from_model(existing)
        required = {rule.ticker for rule in monitor.rules}
        series: dict[str, list[tuple[str, Decimal]]] = {
            ticker: [] for ticker in required
        }
        for observation in self._prices.observations(dataset_id):
            if (
                observation.ticker in series
                and date.fromisoformat(observation.date) <= boundary
            ):
                series[observation.ticker].append(
                    (observation.date, observation.adjusted_close)
                )
        missing = sorted(ticker for ticker, values in series.items() if not values)
        if missing:
            raise MonitoringError(
                "Dataset has no observations on or before as_of for: "
                + ", ".join(missing)
            )
        results = tuple(
            _evaluate_rule(rule, series[rule.ticker]) for rule in monitor.rules
        )
        now = datetime.now(UTC).isoformat()
        model = MonitorEvaluationModel(
            evaluation_id=str(uuid4()),
            monitor_id=monitor_id,
            dataset_id=dataset_id,
            dataset_sha256=dataset.content_sha256,
            as_of=boundary.isoformat(),
            results_json=json.dumps(results, sort_keys=True),
            created_at=now,
        )
        alerts = [
            MonitorAlertModel(
                alert_id=str(uuid4()),
                evaluation_id=model.evaluation_id,
                monitor_id=monitor_id,
                rule_id=result["rule_id"],
                evidence_json=json.dumps(result, sort_keys=True),
                created_at=now,
            )
            for result in results
            if result["triggered"]
        ]
        with self._sessions.begin() as session:
            session.add(model)
            session.flush()
            session.add_all(alerts)
        return _evaluation_from_model(model)

    def list_alerts(
        self, *, monitor_id: str | None = None, status: str | None = None
    ) -> tuple[MonitorAlert, ...]:
        if status not in {None, "open", "acknowledged"}:
            raise MonitoringError("Alert status must be open or acknowledged")
        with self._sessions() as session:
            statement = select(MonitorAlertModel).order_by(
                MonitorAlertModel.created_at, MonitorAlertModel.alert_id
            )
            if monitor_id is not None:
                statement = statement.where(MonitorAlertModel.monitor_id == monitor_id)
            models = session.scalars(statement).all()
            acknowledgements = {
                item.alert_id
                for item in session.scalars(select(AlertAcknowledgementModel)).all()
            }
        alerts = tuple(
            _alert_from_model(model, model.alert_id in acknowledgements)
            for model in models
        )
        return tuple(
            alert for alert in alerts if status is None or alert.status == status
        )

    def acknowledge(
        self, alert_id: str, *, note: str, actor: str = "human_user"
    ) -> AlertAcknowledgement:
        note = note.strip()
        if not note:
            raise MonitoringError("Acknowledgement note is required")
        with self._sessions() as session:
            alert = session.get(MonitorAlertModel, alert_id)
            if alert is None:
                raise MonitoringError(f"Alert not found: {alert_id}")
            existing = session.scalar(
                select(AlertAcknowledgementModel).where(
                    AlertAcknowledgementModel.alert_id == alert_id
                )
            )
            if existing is not None:
                raise MonitoringError(f"Alert already acknowledged: {alert_id}")
        model = AlertAcknowledgementModel(
            acknowledgement_id=str(uuid4()),
            alert_id=alert_id,
            note=note,
            actor=actor,
            acknowledged_at=datetime.now(UTC).isoformat(),
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _acknowledgement_from_model(model)


def _parse_rules(payload: bytes) -> tuple[MonitorRule, ...]:
    try:
        raw = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MonitoringError("Rules must be valid UTF-8 JSON") from error
    if not isinstance(raw, list) or not raw:
        raise MonitoringError("Rules JSON must be a nonempty array")
    rules = []
    seen = set()
    required = {"rule_id", "type", "ticker", "threshold"}
    for index, item in enumerate(raw):
        if not isinstance(item, dict) or set(item) != required:
            raise MonitoringError(
                f"Rule {index} must contain exactly {sorted(required)}"
            )
        rule_id = item["rule_id"]
        if not isinstance(rule_id, str) or not _IDENTIFIER.fullmatch(rule_id):
            raise MonitoringError(f"Rule {index} has invalid rule_id")
        if rule_id in seen:
            raise MonitoringError(f"Duplicate rule_id: {rule_id}")
        rule_type = item["type"]
        if rule_type not in SUPPORTED_RULES:
            raise MonitoringError(f"Unsupported rule type: {rule_type}")
        ticker = item["ticker"]
        if not isinstance(ticker, str) or not _TICKER.fullmatch(ticker):
            raise MonitoringError(f"Rule {index} has invalid ticker")
        try:
            threshold = Decimal(str(item["threshold"]))
        except InvalidOperation as error:
            raise MonitoringError(f"Rule {index} has invalid threshold") from error
        if not threshold.is_finite() or threshold <= 0:
            raise MonitoringError(f"Rule {index} threshold must be positive")
        if rule_type == "drawdown_at_least" and threshold > 1:
            raise MonitoringError("Drawdown threshold must not exceed one")
        seen.add(rule_id)
        rules.append(MonitorRule(rule_id, rule_type, ticker, threshold))
    return tuple(rules)


def _evaluate_rule(rule: MonitorRule, series: list[tuple[str, Decimal]]) -> dict:
    observation_date, latest = series[-1]
    if rule.type == "price_above":
        observed = latest
        triggered = observed > rule.threshold
    elif rule.type == "price_below":
        observed = latest
        triggered = observed < rule.threshold
    else:
        peak = max(value for _, value in series)
        observed = (peak - latest) / peak
        triggered = observed >= rule.threshold
    return {
        "observed": str(observed),
        "observation_date": observation_date,
        "rule_id": rule.rule_id,
        "threshold": str(rule.threshold),
        "ticker": rule.ticker,
        "triggered": triggered,
        "type": rule.type,
    }


def _date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise MonitoringError(f"Invalid as_of date: {value}") from error


def _rule_payload(rule: MonitorRule) -> dict[str, str]:
    return {
        "rule_id": rule.rule_id,
        "type": rule.type,
        "ticker": rule.ticker,
        "threshold": str(rule.threshold),
    }


def _monitor_from_model(model: DecisionMonitorModel) -> DecisionMonitor:
    return DecisionMonitor(
        monitor_id=model.monitor_id,
        run_id=model.run_id,
        name=model.name,
        rules_sha256=model.rules_sha256,
        rules_storage_path=model.rules_storage_path,
        rules=tuple(
            MonitorRule(
                item["rule_id"],
                item["type"],
                item["ticker"],
                Decimal(item["threshold"]),
            )
            for item in json.loads(model.rules_json)
        ),
        created_at=model.created_at,
    )


def _evaluation_from_model(model: MonitorEvaluationModel) -> MonitorEvaluation:
    return MonitorEvaluation(
        evaluation_id=model.evaluation_id,
        monitor_id=model.monitor_id,
        dataset_id=model.dataset_id,
        dataset_sha256=model.dataset_sha256,
        as_of=model.as_of,
        results=tuple(json.loads(model.results_json)),
        created_at=model.created_at,
    )


def _alert_from_model(model: MonitorAlertModel, acknowledged: bool) -> MonitorAlert:
    return MonitorAlert(
        alert_id=model.alert_id,
        evaluation_id=model.evaluation_id,
        monitor_id=model.monitor_id,
        rule_id=model.rule_id,
        evidence=json.loads(model.evidence_json),
        status="acknowledged" if acknowledged else "open",
        created_at=model.created_at,
    )


def _acknowledgement_from_model(
    model: AlertAcknowledgementModel,
) -> AlertAcknowledgement:
    return AlertAcknowledgement(
        acknowledgement_id=model.acknowledgement_id,
        alert_id=model.alert_id,
        note=model.note,
        actor=model.actor,
        acknowledged_at=model.acknowledged_at,
    )
