"""SQLAlchemy ORM models for durable application state."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String
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
