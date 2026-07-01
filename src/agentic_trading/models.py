"""SQLAlchemy ORM models for durable application state."""

from __future__ import annotations

from sqlalchemy import (
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ResearchRunModel(Base):
    __tablename__ = "research_runs"

    run_id: Mapped[str] = mapped_column(String, primary_key=True)
    memo_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    workflow_version: Mapped[str] = mapped_column(String, nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    as_of: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)


class TransitionEventModel(Base):
    __tablename__ = "transition_events"
    __table_args__ = (Index("transition_events_run_id", "run_id", "event_id"),)

    event_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("research_runs.run_id"), nullable=False
    )
    from_state: Mapped[str | None] = mapped_column(String)
    to_state: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(String)


class SourceDocumentModel(Base):
    __tablename__ = "source_documents"
    __table_args__ = (
        UniqueConstraint(
            "run_id", "source_identifier", "content_sha256", name="uq_source_capture"
        ),
        UniqueConstraint("source_id", "run_id", name="uq_source_document_run"),
        Index("source_documents_run_id", "run_id", "source_id"),
    )

    source_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("research_runs.run_id"), nullable=False
    )
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    publisher: Mapped[str] = mapped_column(String, nullable=False)
    canonical_url: Mapped[str] = mapped_column(String, nullable=False)
    source_identifier: Mapped[str] = mapped_column(String, nullable=False)
    published_at: Mapped[str | None] = mapped_column(String)
    retrieved_at: Mapped[str] = mapped_column(String, nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String, nullable=False)


class CandidateClaimModel(Base):
    __tablename__ = "candidate_claims"
    __table_args__ = (
        ForeignKeyConstraint(
            ["source_id", "run_id"],
            ["source_documents.source_id", "source_documents.run_id"],
            name="fk_candidate_claim_source_run",
        ),
        UniqueConstraint(
            "run_id",
            "source_id",
            "taxonomy",
            "concept",
            "unit",
            "period_end",
            name="uq_candidate_fact_observation",
        ),
        Index("candidate_claims_run_id", "run_id", "claim_id"),
    )

    claim_id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, nullable=False)
    source_id: Mapped[str] = mapped_column(String, nullable=False)
    claim_type: Mapped[str] = mapped_column(String, nullable=False)
    statement: Mapped[str] = mapped_column(String, nullable=False)
    taxonomy: Mapped[str] = mapped_column(String, nullable=False)
    concept: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    numeric_value: Mapped[str] = mapped_column(String, nullable=False)
    period_start: Mapped[str | None] = mapped_column(String)
    period_end: Mapped[str] = mapped_column(String, nullable=False)
    accession_number: Mapped[str] = mapped_column(String, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String, nullable=False)
    extracted_at: Mapped[str] = mapped_column(String, nullable=False)
