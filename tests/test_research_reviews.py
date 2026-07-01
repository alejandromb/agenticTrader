import json
import threading
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
from sqlalchemy.orm import Session

from agentic_trading.cli import main
from agentic_trading.dashboard import create_dashboard_server
from agentic_trading.dashboard_workspace import DashboardWorkspaceService
from agentic_trading.database import create_sqlite_engine
from agentic_trading.market_data import SqlitePriceDatasetRepository
from agentic_trading.migrations import upgrade_database
from agentic_trading.models import (
    AnalysisArtifactModel,
    CandidateClaimModel,
    HumanDispositionEventModel,
    InvestmentMemoArtifactModel,
    MonitorAlertModel,
    ResearchRunModel,
    SourceDocumentModel,
)
from agentic_trading.monitoring import SqliteDecisionMonitoring
from agentic_trading.research_reviews import (
    ResearchReviewError,
    SqliteResearchReviewRepository,
)

FIXTURES = Path(__file__).parent / "fixtures"


def memo(ticker: str, *, financials: str, limitations: list[str]) -> dict:
    return {
        "subject": {"ticker": ticker},
        "executive_view": {
            "thesis": "Durable business",
            "counter_thesis": "Competitive pressure",
            "conclusion": "Continue review",
        },
        "sections": {
            "business": {"summary": "Business unchanged"},
            "financials": {"summary": financials},
        },
        "uncertainties": [
            {"description": limitation, "impact": "Limits conclusions"}
            for limitation in limitations
        ],
    }


def claim(
    run_id: str,
    source_id: str,
    claim_id: str,
    concept: str,
    value: str,
    period_end: str,
    *,
    period_start: str | None = None,
) -> CandidateClaimModel:
    return CandidateClaimModel(
        claim_id=claim_id,
        run_id=run_id,
        source_id=source_id,
        claim_type="fact",
        statement=f"{concept} was {value}",
        taxonomy="us-gaap",
        concept=concept,
        label=concept,
        unit="USD",
        numeric_value=value,
        period_start=period_start,
        period_end=period_end,
        accession_number=f"accession-{run_id}",
        extraction_method="fixture",
        extracted_at="2026-01-01T00:00:00+00:00",
    )


def add_run(
    session: Session,
    *,
    run_id: str,
    as_of: str,
    ticker: str = "AAPL",
    state: str = "complete",
    include_memo: bool = True,
    current: bool = False,
) -> None:
    source_id = f"source-{run_id}"
    analysis_id = f"analysis-{run_id}"
    session.add(
        ResearchRunModel(
            run_id=run_id,
            memo_id=f"memo-name-{run_id}",
            workflow_version="fixture",
            state=state,
            as_of=as_of,
            created_at=as_of,
            updated_at=as_of,
        )
    )
    session.flush()
    session.add(
        SourceDocumentModel(
            source_id=source_id,
            run_id=run_id,
            source_type="sec_filing",
            title="Fixture filing",
            publisher="SEC",
            canonical_url=f"https://example.test/{run_id}",
            source_identifier=f"source-identifier-{run_id}",
            published_at=as_of,
            retrieved_at=as_of,
            content_sha256=("a" if not current else "b") * 64,
            size_bytes=100,
            storage_path=f"/fixture/{run_id}",
        )
    )
    session.add(
        AnalysisArtifactModel(
            artifact_id=analysis_id,
            run_id=run_id,
            artifact_type="financial_analysis",
            schema_version="1.0.0",
            provider="fixture",
            model="fixture",
            provider_response_id=f"response-{run_id}",
            prompt_version="fixture",
            evidence_gaps_json="[]",
            content_json="{}",
            created_at=as_of,
            input_tokens=None,
            output_tokens=None,
            request_duration_ms=None,
        )
    )
    session.flush()
    if include_memo:
        limitations = (
            ["Common limitation", "New limitation"]
            if current
            else ["Common limitation.", "Old limitation"]
        )
        session.add(
            InvestmentMemoArtifactModel(
                artifact_id=f"memo-{run_id}",
                run_id=run_id,
                analysis_artifact_id=analysis_id,
                schema_version="2.0.0",
                content_json=json.dumps(
                    memo(
                        ticker,
                        financials=(
                            "Current financials" if current else "Old financials"
                        ),
                        limitations=limitations,
                    )
                ),
                created_at=as_of,
            )
        )
    session.add(
        HumanDispositionEventModel(
            run_id=run_id,
            status="watch",
            rationale="Fixture disposition",
            actor="human_user",
            decided_at=as_of,
        )
    )
    if current:
        claims = [
            claim(
                run_id, source_id, f"{run_id}-revenue", "Revenue", "120", "2025-12-31"
            ),
            claim(run_id, source_id, f"{run_id}-cash", "Cash", "55", "2024-12-31"),
            claim(run_id, source_id, f"{run_id}-assets", "Assets", "200", "2024-12-31"),
            claim(run_id, source_id, f"{run_id}-debt", "Debt", "30", "2025-12-31"),
        ]
    else:
        claims = [
            claim(
                run_id, source_id, f"{run_id}-revenue", "Revenue", "100", "2024-12-31"
            ),
            claim(run_id, source_id, f"{run_id}-cash", "Cash", "50", "2024-12-31"),
            claim(run_id, source_id, f"{run_id}-assets", "Assets", "200", "2024-12-31"),
            claim(
                run_id, source_id, f"{run_id}-legacy", "LegacyMetric", "7", "2024-12-31"
            ),
        ]
    session.add_all(claims)


def setup_reviews(tmp_path):
    database = tmp_path / "state.db"
    artifacts = tmp_path / "artifacts"
    upgrade_database(database)
    with Session(create_sqlite_engine(database)) as session, session.begin():
        add_run(
            session,
            run_id="baseline",
            as_of="2025-01-01T00:00:00+00:00",
        )
        add_run(
            session,
            run_id="current",
            as_of="2026-01-01T00:00:00+00:00",
            current=True,
        )
    dataset = SqlitePriceDatasetRepository(database, artifacts).import_csv(
        FIXTURES / "prices-valid.csv", source="Review fixture"
    )
    monitoring = SqliteDecisionMonitoring(database, artifacts)
    monitor = monitoring.create_monitor(
        run_id="baseline",
        name="Baseline watch",
        rules_path=FIXTURES / "monitor-rules.json",
    )
    monitoring.evaluate(
        monitor.monitor_id, dataset_id=dataset.dataset_id, as_of="2025-01-06"
    )
    alert = monitoring.list_alerts(monitor_id=monitor.monitor_id)[0]
    monitoring.acknowledge(alert.alert_id, note="Reviewed before research refresh")
    monitoring.evaluate(
        monitor.monitor_id, dataset_id=dataset.dataset_id, as_of="2027-01-06"
    )
    return database, artifacts


def test_review_preserves_period_semantics_and_all_delta_categories(tmp_path) -> None:
    database, _ = setup_reviews(tmp_path)
    reviews = SqliteResearchReviewRepository(database)

    review = reviews.compare("baseline", "current")

    assert review.ticker == "AAPL"
    claim_by_concept = {
        (item["identity"]["concept"], item["identity"]["period_end"]): item
        for item in review.content["claim_deltas"]
    }
    assert claim_by_concept[("Cash", "2024-12-31")]["status"] == "changed"
    assert claim_by_concept[("Assets", "2024-12-31")]["status"] == "unchanged"
    assert claim_by_concept[("Revenue", "2024-12-31")]["status"] == "removed"
    assert claim_by_concept[("Revenue", "2025-12-31")]["status"] == "added"
    assert claim_by_concept[("LegacyMetric", "2024-12-31")]["status"] == "removed"
    assert claim_by_concept[("Debt", "2025-12-31")]["status"] == "added"

    metrics = {item["concept"]: item for item in review.content["metric_deltas"]}
    assert metrics["Revenue"]["period_shift"] is True
    assert metrics["Revenue"]["absolute_change"] == "20"
    assert "revision" not in json.dumps(review.content).lower()
    assert metrics["Cash"]["period_shift"] is False
    assert metrics["Cash"]["absolute_change"] == "5"

    assert review.content["limitations"] == {
        "added": ["New limitation"],
        "resolved": ["Old limitation"],
        "unchanged": ["Common limitation"],
    }
    assert [item["section"] for item in review.content["section_deltas"]] == [
        "sections.financials"
    ]
    assert len(review.content["linked_alerts"]) == 2
    assert {item["status"] for item in review.content["linked_alerts"]} == {
        "acknowledged",
        "open",
    }


def test_comparison_is_idempotent_and_reconstructable_after_restart(tmp_path) -> None:
    database, _ = setup_reviews(tmp_path)
    first = SqliteResearchReviewRepository(database).compare("baseline", "current")

    restarted = SqliteResearchReviewRepository(database)
    repeated = restarted.compare("baseline", "current")

    assert repeated == first
    assert restarted.get(first.review_id) == first
    assert restarted.list_reviews() == (first,)

    with pytest.raises(ResearchReviewError, match="must differ"):
        restarted.compare("baseline", "baseline")


def test_human_outcome_is_append_only(tmp_path) -> None:
    database, _ = setup_reviews(tmp_path)
    reviews = SqliteResearchReviewRepository(database)
    review = reviews.compare("baseline", "current")
    with Session(create_sqlite_engine(database)) as session:
        before = {
            "memos": [
                item.content_json
                for item in session.query(InvestmentMemoArtifactModel)
                .order_by(InvestmentMemoArtifactModel.artifact_id)
                .all()
            ],
            "sources": [
                item.content_sha256
                for item in session.query(SourceDocumentModel)
                .order_by(SourceDocumentModel.source_id)
                .all()
            ],
            "alerts": [
                item.evidence_json
                for item in session.query(MonitorAlertModel)
                .order_by(MonitorAlertModel.alert_id)
                .all()
            ],
        }

    outcome = reviews.record_outcome(
        review.review_id,
        outcome="investigate",
        rationale="Review the new debt evidence",
    )

    assert reviews.outcome_for_review(review.review_id) == outcome
    assert reviews.get(review.review_id) == review
    with Session(create_sqlite_engine(database)) as session:
        after = {
            "memos": [
                item.content_json
                for item in session.query(InvestmentMemoArtifactModel)
                .order_by(InvestmentMemoArtifactModel.artifact_id)
                .all()
            ],
            "sources": [
                item.content_sha256
                for item in session.query(SourceDocumentModel)
                .order_by(SourceDocumentModel.source_id)
                .all()
            ],
            "alerts": [
                item.evidence_json
                for item in session.query(MonitorAlertModel)
                .order_by(MonitorAlertModel.alert_id)
                .all()
            ],
        }
    assert after == before
    with pytest.raises(ResearchReviewError, match="already has an outcome"):
        reviews.record_outcome(
            review.review_id,
            outcome="no_thesis_change",
            rationale="Second outcome",
        )


def test_outcome_validation_fails_explicitly(tmp_path) -> None:
    database, _ = setup_reviews(tmp_path)
    reviews = SqliteResearchReviewRepository(database)
    review = reviews.compare("baseline", "current")

    with pytest.raises(ResearchReviewError, match="Invalid"):
        reviews.record_outcome(review.review_id, outcome="buy", rationale="Unsupported")
    with pytest.raises(ResearchReviewError, match="rationale is required"):
        reviews.record_outcome(review.review_id, outcome="investigate", rationale="   ")


def test_complete_cli_review_workflow(tmp_path, capsys) -> None:
    database, _ = setup_reviews(tmp_path)

    compare_args = [
        "compare-research",
        "baseline",
        "current",
        "--database",
        str(database),
    ]
    assert main(compare_args) == 0
    review = json.loads(capsys.readouterr().out)
    assert main(compare_args) == 0
    assert json.loads(capsys.readouterr().out) == review

    assert (
        main(
            [
                "record-review-outcome",
                review["review_id"],
                "revise_thesis",
                "--rationale",
                "New evidence changed the tracked thesis",
                "--database",
                str(database),
            ]
        )
        == 0
    )
    recorded = json.loads(capsys.readouterr().out)
    assert recorded["outcome"] == "revise_thesis"

    assert (
        main(
            [
                "show-research-review",
                review["review_id"],
                "--database",
                str(database),
            ]
        )
        == 0
    )
    shown = json.loads(capsys.readouterr().out)
    assert shown["review_id"] == review["review_id"]
    assert shown["human_outcome"]["outcome"] == "revise_thesis"


def test_dashboard_workspace_review_lifecycle(tmp_path) -> None:
    database, artifacts = setup_reviews(tmp_path)
    workspace = DashboardWorkspaceService(database, artifacts)

    review = workspace.compare_research("baseline", "current")
    assert workspace.review(review["review_id"])["ticker"] == "AAPL"
    assert workspace.snapshot()["reviews"][0]["review_id"] == review["review_id"]

    outcome = workspace.record_review_outcome(
        review["review_id"],
        outcome="investigate",
        rationale="Review refreshed evidence",
    )
    assert outcome["outcome"] == "investigate"
    assert workspace.review(review["review_id"])["human_outcome"] == outcome


def test_dashboard_http_review_lifecycle(tmp_path) -> None:
    database, artifacts = setup_reviews(tmp_path)
    server = create_dashboard_server(
        host="127.0.0.1",
        port=0,
        database_path=database,
        artifact_root=artifacts,
        research_runner=lambda ticker, question: {},
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(f"{base}/api/config") as response:  # noqa: S310
            token = json.load(response)["csrf_token"]

        def post(path: str, payload: dict):
            request = Request(
                f"{base}{path}",
                data=json.dumps(payload).encode(),
                headers={
                    "Content-Type": "application/json",
                    "X-Agentic-CSRF": token,
                },
                method="POST",
            )
            with urlopen(request) as response:  # noqa: S310
                return response.status, json.load(response)

        status, review = post(
            "/api/reviews",
            {"baseline_run_id": "baseline", "current_run_id": "current"},
        )
        assert status == 201
        with urlopen(  # noqa: S310
            f"{base}/api/reviews/{review['review_id']}"
        ) as response:
            shown = json.load(response)
        assert shown["ticker"] == "AAPL"

        status, outcome = post(
            f"/api/reviews/{review['review_id']}/outcome",
            {"outcome": "investigate", "rationale": "Review via dashboard"},
        )
        assert status == 201
        assert outcome["outcome"] == "investigate"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize(
    ("ticker", "state", "include_memo", "as_of", "message"),
    [
        ("MSFT", "complete", True, "2026-01-01T00:00:00+00:00", "tickers"),
        ("AAPL", "analyzing", True, "2026-01-01T00:00:00+00:00", "complete"),
        ("AAPL", "complete", False, "2026-01-01T00:00:00+00:00", "memos"),
        ("AAPL", "complete", True, "2024-01-01T00:00:00+00:00", "after baseline"),
    ],
)
def test_ineligible_pairs_fail_explicitly(
    tmp_path, ticker, state, include_memo, as_of, message
) -> None:
    database = tmp_path / "state.db"
    upgrade_database(database)
    with Session(create_sqlite_engine(database)) as session, session.begin():
        add_run(
            session,
            run_id="baseline",
            as_of="2025-01-01T00:00:00+00:00",
        )
        add_run(
            session,
            run_id="candidate",
            as_of=as_of,
            ticker=ticker,
            state=state,
            include_memo=include_memo,
            current=True,
        )

    with pytest.raises(ResearchReviewError, match=message):
        SqliteResearchReviewRepository(database).compare("baseline", "candidate")
