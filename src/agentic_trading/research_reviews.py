"""Deterministic comparison of completed same-company research records."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import (
    AlertAcknowledgementModel,
    CandidateClaimModel,
    DecisionMonitorModel,
    InvestmentMemoArtifactModel,
    MonitorAlertModel,
    MonitorEvaluationModel,
    ResearchReviewModel,
    ResearchReviewOutcomeModel,
    ResearchRunModel,
)

REVIEW_OUTCOMES = {
    "no_thesis_change",
    "revise_thesis",
    "investigate",
    "close_watch",
}


class ResearchReviewError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ResearchReview:
    review_id: str
    baseline_run_id: str
    current_run_id: str
    baseline_memo_id: str
    current_memo_id: str
    ticker: str
    content: dict
    created_at: str


@dataclass(frozen=True, slots=True)
class ResearchReviewOutcome:
    outcome_id: str
    review_id: str
    outcome: str
    rationale: str
    actor: str
    recorded_at: str


class SqliteResearchReviewRepository:
    def __init__(self, database_path: Path) -> None:
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )

    def compare(self, baseline_run_id: str, current_run_id: str) -> ResearchReview:
        if baseline_run_id == current_run_id:
            raise ResearchReviewError("Baseline and current runs must differ")
        with self._sessions() as session:
            existing = session.scalar(
                select(ResearchReviewModel).where(
                    ResearchReviewModel.baseline_run_id == baseline_run_id,
                    ResearchReviewModel.current_run_id == current_run_id,
                )
            )
            if existing is not None:
                return _review_from_model(existing)
            baseline_run = session.get(ResearchRunModel, baseline_run_id)
            current_run = session.get(ResearchRunModel, current_run_id)
            if baseline_run is None:
                raise ResearchReviewError(f"Research run not found: {baseline_run_id}")
            if current_run is None:
                raise ResearchReviewError(f"Research run not found: {current_run_id}")
            if baseline_run.state != "complete" or current_run.state != "complete":
                raise ResearchReviewError("Both research runs must be complete")
            if _timestamp(current_run.as_of) <= _timestamp(baseline_run.as_of):
                raise ResearchReviewError("Current run as_of must be after baseline")
            baseline_memo = session.scalar(
                select(InvestmentMemoArtifactModel).where(
                    InvestmentMemoArtifactModel.run_id == baseline_run_id
                )
            )
            current_memo = session.scalar(
                select(InvestmentMemoArtifactModel).where(
                    InvestmentMemoArtifactModel.run_id == current_run_id
                )
            )
            if baseline_memo is None or current_memo is None:
                raise ResearchReviewError("Both research runs require canonical memos")
            baseline_content = json.loads(baseline_memo.content_json)
            current_content = json.loads(current_memo.content_json)
            baseline_ticker = baseline_content["subject"]["ticker"]
            current_ticker = current_content["subject"]["ticker"]
            if baseline_ticker != current_ticker:
                raise ResearchReviewError("Research memo tickers must match")
            baseline_claims = session.scalars(
                select(CandidateClaimModel).where(
                    CandidateClaimModel.run_id == baseline_run_id
                )
            ).all()
            current_claims = session.scalars(
                select(CandidateClaimModel).where(
                    CandidateClaimModel.run_id == current_run_id
                )
            ).all()
            content = {
                "warning": (
                    "Differences are descriptive research evidence, not a thesis "
                    "judgment or investment recommendation."
                ),
                "baseline": {
                    "run_id": baseline_run_id,
                    "memo_id": baseline_memo.artifact_id,
                    "as_of": baseline_run.as_of,
                },
                "current": {
                    "run_id": current_run_id,
                    "memo_id": current_memo.artifact_id,
                    "as_of": current_run.as_of,
                },
                "claim_deltas": _claim_deltas(baseline_claims, current_claims),
                "metric_deltas": _metric_deltas(baseline_claims, current_claims),
                "limitations": _limitation_deltas(baseline_content, current_content),
                "section_deltas": _section_deltas(baseline_content, current_content),
                "linked_alerts": _linked_alerts(
                    session,
                    baseline_run_id,
                    baseline_as_of=baseline_run.as_of,
                    current_as_of=current_run.as_of,
                ),
            }
            model = ResearchReviewModel(
                review_id=str(uuid4()),
                baseline_run_id=baseline_run_id,
                current_run_id=current_run_id,
                baseline_memo_id=baseline_memo.artifact_id,
                current_memo_id=current_memo.artifact_id,
                ticker=baseline_ticker,
                content_json=json.dumps(content, sort_keys=True),
                created_at=datetime.now(UTC).isoformat(),
            )
        with self._sessions.begin() as session:
            session.add(model)
        return _review_from_model(model)

    def get(self, review_id: str) -> ResearchReview:
        with self._sessions() as session:
            model = session.get(ResearchReviewModel, review_id)
            if model is None:
                raise ResearchReviewError(f"Research review not found: {review_id}")
            return _review_from_model(model)

    def record_outcome(
        self,
        review_id: str,
        *,
        outcome: str,
        rationale: str,
        actor: str = "human_user",
    ) -> ResearchReviewOutcome:
        if outcome not in REVIEW_OUTCOMES:
            raise ResearchReviewError(f"Invalid research review outcome: {outcome}")
        rationale = rationale.strip()
        if not rationale:
            raise ResearchReviewError("Review outcome rationale is required")
        with self._sessions() as session:
            if session.get(ResearchReviewModel, review_id) is None:
                raise ResearchReviewError(f"Research review not found: {review_id}")
            existing = session.scalar(
                select(ResearchReviewOutcomeModel).where(
                    ResearchReviewOutcomeModel.review_id == review_id
                )
            )
            if existing is not None:
                raise ResearchReviewError(
                    f"Research review already has an outcome: {review_id}"
                )
        model = ResearchReviewOutcomeModel(
            outcome_id=str(uuid4()),
            review_id=review_id,
            outcome=outcome,
            rationale=rationale,
            actor=actor,
            recorded_at=datetime.now(UTC).isoformat(),
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _outcome_from_model(model)

    def outcome_for_review(self, review_id: str) -> ResearchReviewOutcome | None:
        with self._sessions() as session:
            model = session.scalar(
                select(ResearchReviewOutcomeModel).where(
                    ResearchReviewOutcomeModel.review_id == review_id
                )
            )
            return _outcome_from_model(model) if model is not None else None


def _claim_deltas(baseline: list, current: list) -> list[dict]:
    baseline_by_key = {_claim_key(item): item for item in baseline}
    current_by_key = {_claim_key(item): item for item in current}
    deltas = []
    for key in sorted(set(baseline_by_key) | set(current_by_key)):
        before = baseline_by_key.get(key)
        after = current_by_key.get(key)
        if before is None:
            status = "added"
        elif after is None:
            status = "removed"
        elif _claim_value(before) != _claim_value(after):
            status = "changed"
        else:
            status = "unchanged"
        deltas.append(
            {
                "identity": {
                    "claim_type": key[0],
                    "taxonomy": key[1],
                    "concept": key[2],
                    "unit": key[3],
                    "period_start": key[4] or None,
                    "period_end": key[5],
                },
                "status": status,
                "baseline": _claim_payload(before),
                "current": _claim_payload(after),
            }
        )
    return deltas


def _metric_deltas(baseline: list, current: list) -> list[dict]:
    before = _latest_metrics(baseline)
    after = _latest_metrics(current)
    deltas = []
    for key in sorted(set(before) & set(after)):
        left = before[key]
        right = after[key]
        left_value = Decimal(left.numeric_value)
        right_value = Decimal(right.numeric_value)
        percentage_change = None
        if left_value != 0:
            percentage_change = str((right_value - left_value) / abs(left_value))
        deltas.append(
            {
                "claim_type": key[0],
                "taxonomy": key[1],
                "concept": key[2],
                "unit": key[3],
                "baseline_claim_id": left.claim_id,
                "baseline_period_start": left.period_start,
                "baseline_period_end": left.period_end,
                "baseline_value": left.numeric_value,
                "current_claim_id": right.claim_id,
                "current_period_start": right.period_start,
                "current_period_end": right.period_end,
                "current_value": right.numeric_value,
                "absolute_change": str(right_value - left_value),
                "percentage_change": percentage_change,
                "period_shift": (left.period_start, left.period_end)
                != (right.period_start, right.period_end),
            }
        )
    return deltas


def _latest_metrics(claims: list) -> dict[tuple[str, str, str, str], object]:
    latest = {}
    for claim in claims:
        if claim.numeric_value is None:
            continue
        key = (claim.claim_type, claim.taxonomy, claim.concept, claim.unit)
        previous = latest.get(key)
        if previous is None or (
            claim.period_end,
            claim.period_start or "",
            claim.claim_id,
        ) > (previous.period_end, previous.period_start or "", previous.claim_id):
            latest[key] = claim
    return latest


def _limitation_deltas(baseline: dict, current: dict) -> dict[str, list[str]]:
    before = _normalized_limitations(baseline)
    after = _normalized_limitations(current)
    return {
        "added": [after[key] for key in sorted(set(after) - set(before))],
        "resolved": [before[key] for key in sorted(set(before) - set(after))],
        "unchanged": [after[key] for key in sorted(set(before) & set(after))],
    }


def _normalized_limitations(memo: dict) -> dict[str, str]:
    values = {}
    for item in memo.get("uncertainties", []):
        description = item["description"].strip()
        key = re.sub(r"[\s.]+$", "", description.casefold())
        values.setdefault(key, description)
    return values


def _section_deltas(baseline: dict, current: dict) -> list[dict]:
    before = _sections(baseline)
    after = _sections(current)
    deltas = []
    for name in sorted(set(before) | set(after)):
        left = before.get(name)
        right = after.get(name)
        left_hash = _hash(left) if left is not None else None
        right_hash = _hash(right) if right is not None else None
        if left_hash == right_hash:
            continue
        deltas.append(
            {
                "section": name,
                "baseline_summary": left,
                "baseline_sha256": left_hash,
                "current_summary": right,
                "current_sha256": right_hash,
            }
        )
    return deltas


def _sections(memo: dict) -> dict[str, str]:
    values = {
        f"sections.{name}": section["summary"]
        for name, section in memo.get("sections", {}).items()
    }
    executive = memo.get("executive_view", {})
    for name in ("thesis", "counter_thesis", "conclusion"):
        if name in executive:
            values[f"executive_view.{name}"] = executive[name]
    return values


def _linked_alerts(
    session, baseline_run_id: str, *, baseline_as_of: str, current_as_of: str
) -> list[dict]:
    monitor_ids = session.scalars(
        select(DecisionMonitorModel.monitor_id).where(
            DecisionMonitorModel.run_id == baseline_run_id
        )
    ).all()
    if not monitor_ids:
        return []
    alerts = session.scalars(
        select(MonitorAlertModel)
        .where(MonitorAlertModel.monitor_id.in_(monitor_ids))
        .order_by(MonitorAlertModel.created_at, MonitorAlertModel.alert_id)
    ).all()
    evaluations = {
        item.evaluation_id: item
        for item in session.scalars(
            select(MonitorEvaluationModel).where(
                MonitorEvaluationModel.evaluation_id.in_(
                    [alert.evaluation_id for alert in alerts]
                )
            )
        ).all()
    }
    baseline_date = _timestamp(baseline_as_of).date()
    current_date = _timestamp(current_as_of).date()
    alerts = [
        alert
        for alert in alerts
        if baseline_date
        < datetime.fromisoformat(evaluations[alert.evaluation_id].as_of).date()
        <= current_date
    ]
    acknowledgements = {
        item.alert_id: item
        for item in session.scalars(
            select(AlertAcknowledgementModel).where(
                AlertAcknowledgementModel.alert_id.in_(
                    [alert.alert_id for alert in alerts]
                )
            )
        ).all()
    }
    return [
        {
            "alert_id": alert.alert_id,
            "monitor_id": alert.monitor_id,
            "evaluation_id": alert.evaluation_id,
            "rule_id": alert.rule_id,
            "evidence": json.loads(alert.evidence_json),
            "evaluation_as_of": evaluations[alert.evaluation_id].as_of,
            "status": (
                "acknowledged" if alert.alert_id in acknowledgements else "open"
            ),
            "created_at": alert.created_at,
        }
        for alert in alerts
    ]


def _claim_key(claim) -> tuple[str, str, str, str, str, str]:
    return (
        claim.claim_type,
        claim.taxonomy,
        claim.concept,
        claim.unit,
        claim.period_start or "",
        claim.period_end,
    )


def _claim_value(claim) -> tuple[str | None, str]:
    return claim.numeric_value, claim.statement


def _claim_payload(claim) -> dict | None:
    if claim is None:
        return None
    return {
        "accession_number": claim.accession_number,
        "claim_id": claim.claim_id,
        "numeric_value": claim.numeric_value,
        "source_id": claim.source_id,
        "statement": claim.statement,
    }


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ResearchReviewError(f"Invalid run as_of timestamp: {value}") from error
    if parsed.tzinfo is None:
        raise ResearchReviewError(f"Run as_of timestamp requires timezone: {value}")
    return parsed


def _review_from_model(model: ResearchReviewModel) -> ResearchReview:
    return ResearchReview(
        review_id=model.review_id,
        baseline_run_id=model.baseline_run_id,
        current_run_id=model.current_run_id,
        baseline_memo_id=model.baseline_memo_id,
        current_memo_id=model.current_memo_id,
        ticker=model.ticker,
        content=json.loads(model.content_json),
        created_at=model.created_at,
    )


def _outcome_from_model(model: ResearchReviewOutcomeModel) -> ResearchReviewOutcome:
    return ResearchReviewOutcome(
        outcome_id=model.outcome_id,
        review_id=model.review_id,
        outcome=model.outcome,
        rationale=model.rationale,
        actor=model.actor,
        recorded_at=model.recorded_at,
    )
