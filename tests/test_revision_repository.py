from decimal import Decimal

from agentic_trading.migrations import upgrade_database
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.revision_repository import SqliteRevisionAuditRepository
from agentic_trading.xbrl import CrossFilingRevision


def test_revision_audit_is_persisted_and_visible(tmp_path) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    run = SqliteRunRepository(database).create_run(
        memo_id="memo-1", as_of="2026-03-13T23:59:59Z"
    )
    revision = CrossFilingRevision(
        concept="NetIncomeLoss",
        unit="USD",
        period_start="2024-02-01",
        period_end="2025-01-31",
        original_accession="original",
        original_value=Decimal("10"),
        later_accession="later",
        later_value=Decimal("9"),
        absolute_change=Decimal("-1"),
    )

    repository = SqliteRevisionAuditRepository(database)
    saved = repository.register(run.run_id, revision)

    assert saved.revision.classification == "cross_filing_revision"
    assert repository.list_for_run(run.run_id) == [saved]
