from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError

from agentic_trading.migrations import upgrade_database
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.source_repository import SqliteSourceRepository


def test_source_metadata_is_tied_to_run(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    run = SqliteRunRepository(database).create_run(
        run_id="run-001",
        memo_id="memo-001",
        as_of="2025-10-31T23:59:59Z",
    )
    sources = SqliteSourceRepository(database)

    source = sources.register(
        source_id="source-001",
        run_id=run.run_id,
        source_type="regulatory_filing",
        title="Apple Inc. 2025 Form 10-K",
        publisher="U.S. Securities and Exchange Commission",
        canonical_url="https://www.sec.gov/example",
        source_identifier="SEC accession 0000320193-25-000079",
        published_at="2025-10-31T00:00:00Z",
        retrieved_at="2026-06-30T16:00:00Z",
        content_sha256="a" * 64,
        size_bytes=100,
        storage_path="sha256/aa/" + "a" * 64,
    )

    assert sources.list_for_run(run.run_id) == [source]


def test_source_requires_existing_run(tmp_path: Path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    sources = SqliteSourceRepository(database)

    with pytest.raises(IntegrityError):
        sources.register(
            run_id="missing",
            source_type="regulatory_filing",
            title="Filing",
            publisher="SEC",
            canonical_url="https://www.sec.gov/example",
            source_identifier="SEC accession test",
            retrieved_at="2026-06-30T16:00:00Z",
            content_sha256="a" * 64,
            size_bytes=100,
            storage_path="sha256/aa/" + "a" * 64,
        )
