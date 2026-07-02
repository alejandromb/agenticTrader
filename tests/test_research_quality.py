from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from agentic_trading.database import create_sqlite_engine
from agentic_trading.migrations import upgrade_database
from agentic_trading.models import (
    AnalysisArtifactModel,
    AnalysisInputClaimModel,
    CandidateClaimModel,
    InvestmentMemoArtifactModel,
    ResearchRunModel,
    SourceDocumentModel,
)
from agentic_trading.research_quality import (
    CRITERIA,
    ResearchQualityError,
    SqliteResearchQualityRepository,
)


def scores(value: int = 2) -> dict[str, dict[str, object]]:
    return {
        criterion: {"score": value, "rationale": f"Reviewed {criterion}."}
        for criterion in CRITERIA
    }


def create_evaluable_run(database: Path, *, include_gap: bool = True) -> str:
    upgrade_database(database)
    run_id = "run-quality"
    created = "2026-07-02T12:00:00+00:00"
    memo = {
        "schema_version": "2.0.0",
        "uncertainties": (
            [{"description": "Missing debt maturity evidence."}]
            if include_gap
            else []
        ),
        "human_disposition": {"status": "undecided"},
    }
    with Session(create_sqlite_engine(database)) as session, session.begin():
        session.add(
            ResearchRunModel(
                run_id=run_id,
                memo_id="memo-quality",
                workflow_version="2.0.0",
                state="awaiting_human_disposition",
                as_of="2026-02-01T00:00:00Z",
                created_at=created,
                updated_at=created,
            )
        )
        session.flush()
        session.add(
            SourceDocumentModel(
                source_id="source-quality",
                run_id=run_id,
                source_type="regulatory_filing",
                title="Fixture filing",
                publisher="SEC",
                canonical_url="https://www.sec.gov/fixture",
                source_identifier="fixture-accession",
                published_at=created,
                retrieved_at=created,
                content_sha256="a" * 64,
                size_bytes=100,
                storage_path="artifacts/fixture",
            )
        )
        session.flush()
        session.add(
            CandidateClaimModel(
                claim_id="claim-quality",
                run_id=run_id,
                source_id="source-quality",
                claim_type="fact",
                statement="Revenue was 100 USD.",
                taxonomy="us-gaap",
                concept="Revenue",
                label="Revenue",
                unit="USD",
                numeric_value="100",
                period_start="2025-01-01",
                period_end="2025-12-31",
                accession_number="fixture-accession",
                extraction_method="fixture",
                extracted_at=created,
            )
        )
        session.flush()
        session.add(
            AnalysisArtifactModel(
                artifact_id="analysis-quality",
                run_id=run_id,
                artifact_type="financial_analysis",
                schema_version="1.0.0",
                provider="openai",
                model="fixture-model",
                provider_response_id="fixture-response",
                prompt_version="2.2.0",
                evidence_gaps_json=json.dumps(["Missing debt maturity evidence"]),
                content_json=json.dumps(
                    {"strengths": [{"claim_ids": ["claim-quality"]}]}
                ),
                created_at=created,
                input_tokens=100,
                output_tokens=20,
                request_duration_ms=500,
            )
        )
        session.flush()
        session.add(
            AnalysisInputClaimModel(
                artifact_id="analysis-quality",
                claim_id="claim-quality",
                run_id=run_id,
            )
        )
        session.flush()
        session.add(
            InvestmentMemoArtifactModel(
                artifact_id="memo-artifact-quality",
                run_id=run_id,
                analysis_artifact_id="analysis-quality",
                schema_version="2.0.0",
                content_json=json.dumps(memo),
                created_at=created,
            )
        )
    return run_id


def test_evaluation_derives_acceptance_and_reconstructs_after_restart(
    tmp_path: Path,
) -> None:
    database = tmp_path / "state.db"
    run_id = create_evaluable_run(database)

    evaluation = SqliteResearchQualityRepository(database).evaluate(
        run_id, scores=scores()
    )
    restored = SqliteResearchQualityRepository(database).get(
        evaluation.evaluation_id
    )

    assert evaluation.accepted is True
    assert evaluation.total_score == 12
    assert all(evaluation.gates.values())
    assert restored == evaluation
    assert restored.provenance["prompt_version"] == "2.2.0"
    assert restored.provenance["input_tokens"] == 100


def test_evaluation_fails_visible_gap_gate_and_zero_score(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    run_id = create_evaluable_run(database, include_gap=False)
    scored = scores()
    scored["balance"] = {"score": 0, "rationale": "No credible concern."}

    evaluation = SqliteResearchQualityRepository(database).evaluate(
        run_id, scores=scored
    )

    assert evaluation.accepted is False
    assert evaluation.gates["evidence_gaps_visible"] is False
    assert evaluation.total_score == 10


@pytest.mark.parametrize(
    "invalid_scores",
    [
        {},
        {criterion: {"score": 3, "rationale": "Invalid"} for criterion in CRITERIA},
        {criterion: {"score": 2, "rationale": ""} for criterion in CRITERIA},
    ],
)
def test_invalid_score_records_are_rejected_before_persistence(
    tmp_path: Path, invalid_scores: dict
) -> None:
    database = tmp_path / "state.db"
    run_id = create_evaluable_run(database)
    repository = SqliteResearchQualityRepository(database)

    with pytest.raises(ResearchQualityError):
        repository.evaluate(run_id, scores=invalid_scores)

    assert repository.list_evaluations() == ()


def test_evaluations_are_append_only_and_do_not_mutate_run(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    run_id = create_evaluable_run(database)
    repository = SqliteResearchQualityRepository(database)

    first = repository.evaluate(run_id, scores=scores(1), actor="reviewer-one")
    second = repository.evaluate(run_id, scores=scores(2), actor="reviewer-two")

    assert first.evaluation_id != second.evaluation_id
    assert len(repository.list_evaluations(run_id=run_id)) == 2
    with Session(create_sqlite_engine(database)) as session:
        run = session.get(ResearchRunModel, run_id)
        assert run is not None
        assert run.state == "awaiting_human_disposition"
        assert run.updated_at == "2026-07-02T12:00:00+00:00"
