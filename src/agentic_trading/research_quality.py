"""Versioned, append-only evaluation of persisted research quality."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import (
    AnalysisArtifactModel,
    AnalysisInputClaimModel,
    CandidateClaimModel,
    InvestmentMemoArtifactModel,
    ResearchQualityEvaluationModel,
    ResearchRunModel,
)

RUBRIC_VERSION = "1.0.0"
CRITERIA = (
    "numerical_fidelity",
    "evidence_fidelity",
    "fact_judgment_separation",
    "balance",
    "uncertainty",
    "decision_usefulness",
)
ACCEPTANCE_SCORE = 9


class ResearchQualityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class CriterionScore:
    score: int
    rationale: str


@dataclass(frozen=True, slots=True)
class ResearchQualityEvaluation:
    evaluation_id: str
    run_id: str
    analysis_artifact_id: str
    memo_artifact_id: str
    rubric_version: str
    gates: dict[str, bool]
    scores: dict[str, CriterionScore]
    total_score: int
    accepted: bool
    provenance: dict[str, Any]
    actor: str
    created_at: str


class SqliteResearchQualityRepository:
    def __init__(self, database_path: Path) -> None:
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )

    def evaluate(
        self,
        run_id: str,
        *,
        scores: dict[str, dict[str, Any]],
        actor: str = "human_user",
    ) -> ResearchQualityEvaluation:
        normalized_scores = _validate_scores(scores)
        actor = actor.strip()
        if not actor:
            raise ResearchQualityError("Evaluation actor is required")
        with self._sessions() as session:
            run = session.get(ResearchRunModel, run_id)
            if run is None:
                raise ResearchQualityError(f"Research run not found: {run_id}")
            analysis = session.scalar(
                select(AnalysisArtifactModel)
                .where(AnalysisArtifactModel.run_id == run_id)
                .order_by(AnalysisArtifactModel.created_at.desc())
            )
            memo = session.scalar(
                select(InvestmentMemoArtifactModel).where(
                    InvestmentMemoArtifactModel.run_id == run_id
                )
            )
            if analysis is None or memo is None:
                raise ResearchQualityError(
                    "Research quality evaluation requires analysis and canonical memo"
                )
            gates = _compute_gates(session, run_id, analysis, memo)
            provenance = {
                "run_as_of": run.as_of,
                "workflow_version": run.workflow_version,
                "analysis_schema_version": analysis.schema_version,
                "memo_schema_version": memo.schema_version,
                "provider": analysis.provider,
                "model": analysis.model,
                "provider_response_id": analysis.provider_response_id,
                "prompt_version": analysis.prompt_version,
                "input_tokens": analysis.input_tokens,
                "output_tokens": analysis.output_tokens,
                "request_duration_ms": analysis.request_duration_ms,
            }
        total = sum(item.score for item in normalized_scores.values())
        accepted = (
            all(gates.values())
            and all(item.score > 0 for item in normalized_scores.values())
            and total >= ACCEPTANCE_SCORE
        )
        model = ResearchQualityEvaluationModel(
            evaluation_id=str(uuid4()),
            run_id=run_id,
            analysis_artifact_id=analysis.artifact_id,
            memo_artifact_id=memo.artifact_id,
            rubric_version=RUBRIC_VERSION,
            gates_json=json.dumps(gates, sort_keys=True),
            scores_json=json.dumps(
                {
                    key: {"score": value.score, "rationale": value.rationale}
                    for key, value in normalized_scores.items()
                },
                sort_keys=True,
            ),
            total_score=total,
            accepted=int(accepted),
            provenance_json=json.dumps(provenance, sort_keys=True),
            actor=actor,
            created_at=datetime.now(UTC).isoformat(),
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _from_model(model)

    def get(self, evaluation_id: str) -> ResearchQualityEvaluation:
        with self._sessions() as session:
            model = session.get(ResearchQualityEvaluationModel, evaluation_id)
            if model is None:
                raise ResearchQualityError(
                    f"Research quality evaluation not found: {evaluation_id}"
                )
            return _from_model(model)

    def list_evaluations(
        self, *, run_id: str | None = None
    ) -> tuple[ResearchQualityEvaluation, ...]:
        with self._sessions() as session:
            query = select(ResearchQualityEvaluationModel)
            if run_id is not None:
                query = query.where(ResearchQualityEvaluationModel.run_id == run_id)
            models = session.scalars(
                query.order_by(
                    ResearchQualityEvaluationModel.created_at.desc(),
                    ResearchQualityEvaluationModel.evaluation_id,
                )
            ).all()
            return tuple(_from_model(model) for model in models)


def _validate_scores(
    scores: dict[str, dict[str, Any]],
) -> dict[str, CriterionScore]:
    if not isinstance(scores, dict) or set(scores) != set(CRITERIA):
        raise ResearchQualityError(
            "Scores must contain exactly: " + ", ".join(CRITERIA)
        )
    normalized: dict[str, CriterionScore] = {}
    for criterion in CRITERIA:
        value = scores[criterion]
        if not isinstance(value, dict) or set(value) != {"score", "rationale"}:
            raise ResearchQualityError(
                f"{criterion} must contain score and rationale"
            )
        score = value["score"]
        if (
            isinstance(score, bool)
            or not isinstance(score, int)
            or score not in {0, 1, 2}
        ):
            raise ResearchQualityError(f"{criterion} score must be 0, 1, or 2")
        rationale = value["rationale"]
        if not isinstance(rationale, str) or not rationale.strip():
            raise ResearchQualityError(f"{criterion} rationale is required")
        normalized[criterion] = CriterionScore(score, rationale.strip())
    return normalized


def _compute_gates(
    session: Session,
    run_id: str,
    analysis: AnalysisArtifactModel,
    memo: InvestmentMemoArtifactModel,
) -> dict[str, bool]:
    analysis_content = json.loads(analysis.content_json)
    memo_content = json.loads(memo.content_json)
    cited_claim_ids = _collect_claim_ids(analysis_content)
    input_claim_ids = set(
        session.scalars(
            select(AnalysisInputClaimModel.claim_id).where(
                AnalysisInputClaimModel.artifact_id == analysis.artifact_id
            )
        ).all()
    )
    run_claim_ids = set(
        session.scalars(
            select(CandidateClaimModel.claim_id).where(
                CandidateClaimModel.run_id == run_id
            )
        ).all()
    )
    gaps = {_normalize(item) for item in json.loads(analysis.evidence_gaps_json)}
    limitations = {
        _normalize(item.get("description", ""))
        for item in memo_content.get("uncertainties", [])
        if isinstance(item, dict)
    }
    return {
        "artifacts_present": memo.analysis_artifact_id == analysis.artifact_id,
        "claim_lineage_complete": bool(cited_claim_ids)
        and cited_claim_ids <= input_claim_ids <= run_claim_ids,
        "evidence_gaps_visible": gaps <= limitations,
        "provenance_complete": all(
            (
                analysis.provider,
                analysis.model,
                analysis.provider_response_id,
                analysis.prompt_version,
                analysis.schema_version,
                memo.schema_version,
            )
        ),
        "human_authority_preserved": memo_content.get("human_disposition")
        == {"status": "undecided"},
    }


def _collect_claim_ids(value: Any) -> set[str]:
    if isinstance(value, dict):
        found = (
            set(value.get("claim_ids", []))
            if isinstance(value.get("claim_ids"), list)
            else set()
        )
        for child in value.values():
            found.update(_collect_claim_ids(child))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for child in value:
            found.update(_collect_claim_ids(child))
        return found
    return set()


def _normalize(value: str) -> str:
    return value.strip().rstrip(". ").casefold()


def _from_model(model: ResearchQualityEvaluationModel) -> ResearchQualityEvaluation:
    scores = {
        key: CriterionScore(score=value["score"], rationale=value["rationale"])
        for key, value in json.loads(model.scores_json).items()
    }
    return ResearchQualityEvaluation(
        evaluation_id=model.evaluation_id,
        run_id=model.run_id,
        analysis_artifact_id=model.analysis_artifact_id,
        memo_artifact_id=model.memo_artifact_id,
        rubric_version=model.rubric_version,
        gates=json.loads(model.gates_json),
        scores=scores,
        total_score=model.total_score,
        accepted=bool(model.accepted),
        provenance=json.loads(model.provenance_json),
        actor=model.actor,
        created_at=model.created_at,
    )
