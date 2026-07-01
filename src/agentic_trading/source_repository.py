"""ORM persistence for captured research source documents."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from agentic_trading.database import create_sqlite_engine
from agentic_trading.models import SourceDocumentModel


@dataclass(frozen=True, slots=True)
class SourceDocument:
    source_id: str
    run_id: str
    source_type: str
    title: str
    publisher: str
    canonical_url: str
    source_identifier: str
    published_at: str | None
    retrieved_at: str
    content_sha256: str
    size_bytes: int
    storage_path: str


class SqliteSourceRepository:
    """Persist source metadata through SQLAlchemy."""

    def __init__(self, database_path: Path) -> None:
        engine = create_sqlite_engine(database_path)
        self._sessions = sessionmaker(engine, expire_on_commit=False)

    def register(
        self,
        *,
        run_id: str,
        source_type: str,
        title: str,
        publisher: str,
        canonical_url: str,
        source_identifier: str,
        retrieved_at: str,
        content_sha256: str,
        size_bytes: int,
        storage_path: str,
        published_at: str | None = None,
        source_id: str | None = None,
    ) -> SourceDocument:
        """Register immutable source provenance for a captured artifact."""
        model = SourceDocumentModel(
            source_id=source_id or str(uuid4()),
            run_id=run_id,
            source_type=source_type,
            title=title,
            publisher=publisher,
            canonical_url=canonical_url,
            source_identifier=source_identifier,
            published_at=published_at,
            retrieved_at=retrieved_at,
            content_sha256=content_sha256,
            size_bytes=size_bytes,
            storage_path=storage_path,
        )
        with self._sessions.begin() as session:
            session.add(model)
        return _source_from_model(model)

    def list_for_run(self, run_id: str) -> list[SourceDocument]:
        """Return captured source metadata in stable ID order."""
        with self._sessions() as session:
            models = session.scalars(
                select(SourceDocumentModel)
                .where(SourceDocumentModel.run_id == run_id)
                .order_by(SourceDocumentModel.source_id)
            ).all()
            return [_source_from_model(model) for model in models]


def _source_from_model(model: SourceDocumentModel) -> SourceDocument:
    return SourceDocument(
        source_id=model.source_id,
        run_id=model.run_id,
        source_type=model.source_type,
        title=model.title,
        publisher=model.publisher,
        canonical_url=model.canonical_url,
        source_identifier=model.source_identifier,
        published_at=model.published_at,
        retrieved_at=model.retrieved_at,
        content_sha256=model.content_sha256,
        size_bytes=model.size_bytes,
        storage_path=model.storage_path,
    )
