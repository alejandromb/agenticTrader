"""ORM persistence for structured model analysis artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import sessionmaker

from agentic_trading.analysis import FinancialAnalysis
from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import AnalysisArtifactModel, AnalysisInputClaimModel
from agentic_trading.openai_adapter import GeneratedFinancialAnalysis

ANALYSIS_SCHEMA_VERSION = "1.0.0"
FINANCIAL_PROMPT_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class AnalysisArtifact:
    artifact_id: str
    run_id: str
    artifact_type: str
    schema_version: str
    provider: str
    model: str
    provider_response_id: str
    prompt_version: str
    analysis: FinancialAnalysis
    input_claim_ids: tuple[str, ...]
    created_at: str


class SqliteAnalysisRepository:
    """Persist structured analyses and their exact input-claim lineage."""

    def __init__(self, database_path: Path) -> None:
        engine = create_sqlite_engine(database_path)
        self._sessions = sessionmaker(engine, expire_on_commit=False)

    def save_openai_financial_analysis(
        self,
        *,
        run_id: str,
        generated: GeneratedFinancialAnalysis,
        artifact_id: str | None = None,
    ) -> AnalysisArtifact:
        """Save a validated OpenAI analysis and claim lineage atomically."""
        identifier = artifact_id or str(uuid4())
        created_at = datetime.now(UTC).isoformat()
        model = AnalysisArtifactModel(
            artifact_id=identifier,
            run_id=run_id,
            artifact_type="financial_analysis",
            schema_version=ANALYSIS_SCHEMA_VERSION,
            provider="openai",
            model=generated.model,
            provider_response_id=generated.provider_response_id,
            prompt_version=FINANCIAL_PROMPT_VERSION,
            content_json=generated.analysis.model_dump_json(),
            created_at=created_at,
        )
        with self._sessions.begin() as session:
            session.add(model)
            session.add_all(
                AnalysisInputClaimModel(
                    artifact_id=identifier,
                    claim_id=claim_id,
                    run_id=run_id,
                )
                for claim_id in generated.input_claim_ids
            )
        return AnalysisArtifact(
            artifact_id=identifier,
            run_id=run_id,
            artifact_type=model.artifact_type,
            schema_version=model.schema_version,
            provider=model.provider,
            model=model.model,
            provider_response_id=model.provider_response_id,
            prompt_version=model.prompt_version,
            analysis=FinancialAnalysis.model_validate_json(model.content_json),
            input_claim_ids=generated.input_claim_ids,
            created_at=created_at,
        )
