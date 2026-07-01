"""Canonical investment memo synthesis, validation, and persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.analysis import AnalysisPoint, FinancialAnalysis
from agentic_trading.analysis_repository import AnalysisArtifact
from agentic_trading.claim_repository import CandidateClaim, SqliteClaimRepository
from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import InvestmentMemoArtifactModel
from agentic_trading.repository import ResearchRun
from agentic_trading.sec import CompanyIdentity
from agentic_trading.source_repository import SourceDocument
from agentic_trading.validation import load_json, validate_memo

SCHEMA_VERSION = "1.0.0"
DEFAULT_SCHEMA_PATH = (
    Path(__file__).parents[2] / "schemas/investment-memo-v1.schema.json"
)


@dataclass(frozen=True, slots=True)
class InvestmentMemoArtifact:
    artifact_id: str
    run_id: str
    analysis_artifact_id: str
    schema_version: str
    memo: dict
    created_at: str


class SqliteInvestmentMemoRepository:
    def __init__(self, database_path: Path) -> None:
        self._claim_repository = SqliteClaimRepository(database_path)
        self._sessions = sessionmaker(
            create_sqlite_engine(database_path), expire_on_commit=False
        )

    def synthesize_and_save(
        self,
        *,
        run: ResearchRun,
        company: CompanyIdentity,
        question: str,
        source: SourceDocument,
        claims: list[CandidateClaim],
        analysis: AnalysisArtifact,
    ) -> InvestmentMemoArtifact:
        created_at = datetime.now(UTC).isoformat()
        memo = self._build_memo(
            run=run,
            company=company,
            question=question,
            source=source,
            claims=claims,
            analysis=analysis.analysis,
            created_at=created_at,
        )
        validate_memo(memo, load_json(DEFAULT_SCHEMA_PATH))
        model = InvestmentMemoArtifactModel(
            artifact_id=str(uuid4()),
            run_id=run.run_id,
            analysis_artifact_id=analysis.artifact_id,
            schema_version=SCHEMA_VERSION,
            content_json=json.dumps(memo, sort_keys=True),
            created_at=created_at,
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _from_model(model)

    def latest_for_run(self, run_id: str) -> InvestmentMemoArtifact | None:
        with self._sessions() as session:
            model = session.scalar(
                select(InvestmentMemoArtifactModel).where(
                    InvestmentMemoArtifactModel.run_id == run_id
                )
            )
            return _from_model(model) if model is not None else None

    def _build_memo(
        self,
        *,
        run: ResearchRun,
        company: CompanyIdentity,
        question: str,
        source: SourceDocument,
        claims: list[CandidateClaim],
        analysis: FinancialAnalysis,
        created_at: str,
    ) -> dict:
        memo_claims = [self._memo_claim(claim) for claim in claims]
        evidence = [
            _evidence(claim, source)
            for claim in claims
            if claim.claim_type in {"fact", "filing_statement"}
        ]
        thesis_points = analysis.bull_case or analysis.strengths
        counter_points = (
            analysis.bear_case or analysis.material_risks or analysis.concerns
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "memo_id": run.memo_id,
            "created_at": created_at,
            "as_of": run.as_of,
            "subject": {
                "ticker": company.ticker,
                "company_name": company.name,
                "exchange": "Not verified",
                "security_id": f"CIK-{company.cik}",
            },
            "question": question,
            "horizon": {"label": "Long term", "minimum_years": 3},
            "executive_view": {
                "thesis": _text(thesis_points, "No supported bull case."),
                "counter_thesis": _text(counter_points, "No supported counter-thesis."),
                "conclusion": analysis.summary,
                "claim_ids": _claim_ids((*thesis_points, *counter_points)),
            },
            "sections": {
                "business": _section(analysis.business_quality),
                "financials": _section(
                    (*analysis.strengths, *analysis.concerns, *analysis.trends)
                ),
                "valuation": _section(analysis.valuation),
                "risks": _section(
                    (
                        *analysis.material_risks,
                        *analysis.bear_case,
                        *analysis.devils_advocate,
                    )
                ),
            },
            "claims": memo_claims,
            "evidence": evidence,
            "uncertainties": [
                {
                    "description": limitation,
                    "impact": "This limits the conclusions supported by the memo.",
                }
                for limitation in (
                    *analysis.known_limitations,
                    "The listing exchange was not verified from captured evidence.",
                )
            ],
            "human_disposition": {"status": "undecided"},
        }

    def _memo_claim(self, claim: CandidateClaim) -> dict:
        if claim.claim_type in {"calculation", "assumption_calculation"}:
            lineage = self._claim_repository.calculation_lineage(claim.claim_id)
            if lineage is None or claim.numeric_value is None:
                raise ValueError(f"Calculation lineage missing for {claim.claim_id}")
            formula, input_ids = lineage
            return {
                "claim_id": claim.claim_id,
                "type": "calculation",
                "statement": claim.statement,
                "input_claim_ids": list(input_ids),
                "method": formula,
                "result": {"value": float(claim.numeric_value), "unit": claim.unit},
            }
        return {
            "claim_id": claim.claim_id,
            "type": "fact",
            "statement": claim.statement,
            "evidence_ids": [f"evidence-{claim.claim_id}"],
        }


def _section(points: tuple[AnalysisPoint, ...] | list[AnalysisPoint]) -> dict:
    return {
        "summary": _text(points, "No supported analysis was available."),
        "claim_ids": _claim_ids(points),
    }


def _text(points, fallback: str) -> str:
    return " ".join(point.text for point in points) or fallback


def _claim_ids(points) -> list[str]:
    return list(
        dict.fromkeys(claim_id for point in points for claim_id in point.claim_ids)
    )


def _evidence(claim: CandidateClaim, source: SourceDocument) -> dict:
    value = {
        "evidence_id": f"evidence-{claim.claim_id}",
        "source_type": source.source_type,
        "title": source.title,
        "publisher": source.publisher,
        "url": source.canonical_url,
        "retrieved_at": source.retrieved_at,
        "locator": f"{claim.taxonomy}:{claim.concept}; period {claim.period_end}",
        "support": claim.statement,
        "content_hash": source.content_sha256,
        "source_identifier": source.source_identifier,
    }
    if source.published_at is not None:
        value["published_at"] = source.published_at
    return value


def _from_model(model: InvestmentMemoArtifactModel) -> InvestmentMemoArtifact:
    return InvestmentMemoArtifact(
        artifact_id=model.artifact_id,
        run_id=model.run_id,
        analysis_artifact_id=model.analysis_artifact_id,
        schema_version=model.schema_version,
        memo=json.loads(model.content_json),
        created_at=model.created_at,
    )
