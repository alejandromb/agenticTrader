"""Command-line interface for local Agentic Trading workflows."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

from agentic_trading.analysis_repository import SqliteAnalysisRepository
from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.backtesting import BacktestError, SqliteBacktester
from agentic_trading.claim_repository import SqliteClaimRepository
from agentic_trading.dashboard import DashboardError, serve_dashboard
from agentic_trading.disposition_repository import (
    ALLOWED_DISPOSITIONS,
    SqliteDispositionRepository,
)
from agentic_trading.financials import extract_annual_financial_snapshot
from agentic_trading.market_data import (
    PriceDatasetError,
    SqlitePriceDatasetRepository,
)
from agentic_trading.memo_repository import SqliteInvestmentMemoRepository
from agentic_trading.migrations import upgrade_database
from agentic_trading.monitoring import MonitoringError, SqliteDecisionMonitoring
from agentic_trading.openai_adapter import (
    AnalysisGenerationError,
    OpenAIFinancialAnalysisAdapter,
)
from agentic_trading.portfolio_analytics import (
    PortfolioAnalysisError,
    SqlitePortfolioAnalyzer,
)
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.research import CompanyResearchService
from agentic_trading.research_reviews import (
    REVIEW_OUTCOMES,
    ResearchReviewError,
    SqliteResearchReviewRepository,
)
from agentic_trading.revision_repository import SqliteRevisionAuditRepository
from agentic_trading.screener import ScreenFilters, SqliteResearchScreener
from agentic_trading.sec import SecClient, SecClientError
from agentic_trading.source_repository import SqliteSourceRepository
from agentic_trading.validation import validate_memo_files
from agentic_trading.workflow import WorkflowState
from agentic_trading.xbrl import XbrlFactError, select_filing_fact

DEFAULT_SCHEMA = Path("schemas/investment-memo-v1.schema.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentic-trading")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate-memo", help="validate a memo artifact")
    validate.add_argument("memo", type=Path)
    validate.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)

    filings = commands.add_parser("sec-filings", help="list recent SEC filings")
    filings.add_argument("cik")
    filings.add_argument("--form")

    fetch = commands.add_parser(
        "sec-fetch-latest", help="fetch and store the latest SEC filing"
    )
    fetch.add_argument("cik")
    fetch.add_argument("--form", required=True)
    fetch.add_argument("--artifact-root", type=Path, required=True)
    fetch.add_argument("--database", type=Path)
    fetch.add_argument("--run-id")

    fact = commands.add_parser("sec-fact", help="select an SEC XBRL filing fact")
    fact.add_argument("cik")
    fact.add_argument("accession_number")
    fact.add_argument("concept")
    fact.add_argument("--period-end", required=True)
    fact.add_argument("--taxonomy", default="us-gaap")
    fact.add_argument("--unit", default="USD")

    snapshot = commands.add_parser(
        "sec-financial-snapshot", help="extract minimum annual SEC financials"
    )
    snapshot.add_argument("cik")
    snapshot.add_argument("accession_number")
    snapshot.add_argument("--period-start", required=True)
    snapshot.add_argument("--period-end", required=True)
    snapshot.add_argument("--database", type=Path)
    snapshot.add_argument("--run-id")
    snapshot.add_argument("--source-id")

    initialize = commands.add_parser("init-db", help="initialize local workflow state")
    initialize.add_argument("database", type=Path)

    create = commands.add_parser("create-run", help="create a draft research run")
    create.add_argument("database", type=Path)
    create.add_argument("memo_id")
    create.add_argument("as_of")

    transition = commands.add_parser("transition", help="transition a research run")
    transition.add_argument("database", type=Path)
    transition.add_argument("run_id")
    transition.add_argument("expected_state", type=WorkflowState)
    transition.add_argument("target_state", type=WorkflowState)
    transition.add_argument("--reason")

    analyze = commands.add_parser(
        "analyze-financials", help="generate and persist structured analysis"
    )
    analyze.add_argument("database", type=Path)
    analyze.add_argument("run_id")
    analyze.add_argument("question")

    research = commands.add_parser(
        "research-company", help="run the complete version-two research workflow"
    )
    research.add_argument("ticker")
    research.add_argument("--question", required=True)
    research.add_argument("--form", choices=("10-K", "10-Q"), default="10-K")
    research.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    research.add_argument("--artifact-root", type=Path, default=Path("artifacts"))

    doctor = commands.add_parser("doctor", help="check local runtime configuration")
    doctor.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )

    list_runs = commands.add_parser("list-runs", help="list saved research runs")
    list_runs.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )

    show_run = commands.add_parser("show-run", help="show a saved research run")
    show_run.add_argument("run_id")
    show_run.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )

    disposition = commands.add_parser(
        "record-disposition", help="record the human disposition for a memo"
    )
    disposition.add_argument("run_id")
    disposition.add_argument("status", choices=sorted(ALLOWED_DISPOSITIONS))
    disposition.add_argument("--rationale")
    disposition.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )

    import_prices = commands.add_parser(
        "import-prices", help="import an immutable adjusted-price CSV dataset"
    )
    import_prices.add_argument("csv", type=Path)
    import_prices.add_argument("--source", required=True)
    import_prices.add_argument(
        "--adjustment-note",
        default="Adjusted-close values supplied by dataset source.",
    )

    screen = commands.add_parser(
        "screen-research", help="screen persisted research using as-of metrics"
    )
    screen.add_argument("--as-of", required=True)
    screen.add_argument("--min-revenue-growth", type=Decimal)
    screen.add_argument("--min-operating-margin", type=Decimal)
    screen.add_argument("--min-net-margin", type=Decimal)
    screen.add_argument("--min-current-ratio", type=Decimal)
    screen.add_argument("--min-free-cash-flow", type=Decimal)
    screen.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )

    portfolio = commands.add_parser(
        "analyze-portfolio", help="analyze a hypothetical holdings CSV"
    )
    portfolio.add_argument("holdings", type=Path)
    portfolio.add_argument("--dataset", required=True)
    portfolio.add_argument("--benchmark", required=True)
    portfolio.add_argument("--as-of", required=True)
    portfolio.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    portfolio.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    backtest = commands.add_parser(
        "backtest", help="run a deterministic moving-average simulation"
    )
    backtest.add_argument("dataset")
    backtest.add_argument("--ticker", required=True)
    backtest.add_argument("--benchmark", required=True)
    backtest.add_argument("--short-window", type=int, required=True)
    backtest.add_argument("--long-window", type=int, required=True)
    backtest.add_argument("--initial-cash", type=Decimal, default=Decimal("10000"))
    backtest.add_argument("--transaction-cost-bps", type=Decimal, default=Decimal("10"))
    backtest.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    backtest.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    create_monitor = commands.add_parser(
        "create-monitor", help="create human-defined follow-up criteria"
    )
    create_monitor.add_argument("run_id")
    create_monitor.add_argument("--name", required=True)
    create_monitor.add_argument("--rules", type=Path, required=True)
    create_monitor.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    create_monitor.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    evaluate_monitor = commands.add_parser(
        "evaluate-monitor", help="evaluate a monitor against immutable prices"
    )
    evaluate_monitor.add_argument("monitor_id")
    evaluate_monitor.add_argument("--dataset", required=True)
    evaluate_monitor.add_argument("--as-of", required=True)
    evaluate_monitor.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    evaluate_monitor.add_argument(
        "--artifact-root", type=Path, default=Path("artifacts")
    )
    list_alerts = commands.add_parser(
        "list-alerts", help="list durable decision-monitoring alerts"
    )
    list_alerts.add_argument("--monitor")
    list_alerts.add_argument("--status", choices=("open", "acknowledged"))
    list_alerts.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    list_alerts.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    acknowledge_alert = commands.add_parser(
        "acknowledge-alert", help="append a human alert acknowledgement"
    )
    acknowledge_alert.add_argument("alert_id")
    acknowledge_alert.add_argument("--note", required=True)
    acknowledge_alert.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    acknowledge_alert.add_argument(
        "--artifact-root", type=Path, default=Path("artifacts")
    )
    compare_research = commands.add_parser(
        "compare-research", help="compare two completed same-company research runs"
    )
    compare_research.add_argument("baseline_run_id")
    compare_research.add_argument("current_run_id")
    compare_research.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    show_review = commands.add_parser(
        "show-research-review", help="show a persisted research-refresh review"
    )
    show_review.add_argument("review_id")
    show_review.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    record_review = commands.add_parser(
        "record-review-outcome", help="append a human research-review outcome"
    )
    record_review.add_argument("review_id")
    record_review.add_argument("outcome", choices=sorted(REVIEW_OUTCOMES))
    record_review.add_argument("--rationale", required=True)
    record_review.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    dashboard = commands.add_parser(
        "dashboard", help="serve the loopback-only local research dashboard"
    )
    dashboard.add_argument("--host", default="127.0.0.1")
    dashboard.add_argument("--port", type=int, default=8765)
    dashboard.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    dashboard.add_argument("--artifact-root", type=Path, default=Path("artifacts"))
    import_prices.add_argument(
        "--database", type=Path, default=Path("data/agentic-trading.db")
    )
    import_prices.add_argument("--artifact-root", type=Path, default=Path("artifacts"))

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    args = build_parser().parse_args(argv)

    if args.command == "validate-memo":
        validate_memo_files(args.memo, args.schema)
        print(f"Valid investment memo: {args.memo}")
        return 0

    if args.command == "doctor":
        checks = {
            "database_exists": args.database.exists(),
            "openai_api_key_configured": bool(os.environ.get("OPENAI_API_KEY")),
            "sec_user_agent_configured": bool(os.environ.get("SEC_USER_AGENT")),
        }
        print(json.dumps(checks, sort_keys=True))
        return (
            0
            if all(
                (
                    checks["openai_api_key_configured"],
                    checks["sec_user_agent_configured"],
                )
            )
            else 1
        )

    if args.command == "dashboard":
        try:
            serve_dashboard(
                host=args.host,
                port=args.port,
                database_path=args.database,
                artifact_root=args.artifact_root,
            )
        except DashboardError as error:
            raise SystemExit(str(error)) from error
        return 0

    if args.command == "research-company":
        user_agent = os.environ.get("SEC_USER_AGENT")
        if not user_agent:
            raise SystemExit(
                "SEC_USER_AGENT is required and must identify the application owner"
            )
        try:
            result = CompanyResearchService(
                database_path=args.database,
                artifact_root=args.artifact_root,
                sec_client=SecClient(user_agent),
                analysis_adapter=OpenAIFinancialAnalysisAdapter(),
            ).research(
                ticker=args.ticker.upper(), question=args.question, form=args.form
            )
        except (
            AnalysisGenerationError,
            SecClientError,
            ValueError,
            XbrlFactError,
        ) as error:
            raise SystemExit(str(error)) from error
        print(
            json.dumps(
                {
                    "analysis": result.analysis.analysis.model_dump(),
                    "analysis_artifact_id": result.analysis.artifact_id,
                    "company": result.company.name,
                    "evidence_gaps": result.analysis.evidence_gaps,
                    "filing_accession": result.filing.accession_number,
                    "filing_date": result.filing.filing_date,
                    "filing_form": result.filing.form,
                    "model": result.analysis.model,
                    "memo_artifact_id": result.memo.artifact_id,
                    "model_usage": {
                        "input_tokens": result.analysis.input_tokens,
                        "output_tokens": result.analysis.output_tokens,
                        "request_duration_ms": result.analysis.request_duration_ms,
                    },
                    "prompt_version": result.analysis.prompt_version,
                    "run_id": result.run.run_id,
                    "state": result.run.state,
                    "ticker": result.company.ticker,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command in {
        "sec-filings",
        "sec-fetch-latest",
        "sec-fact",
        "sec-financial-snapshot",
    }:
        user_agent = os.environ.get("SEC_USER_AGENT")
        if not user_agent:
            raise SystemExit(
                "SEC_USER_AGENT is required and must identify the application owner"
            )
        client = SecClient(user_agent)
        if args.command == "sec-financial-snapshot":
            persistence_args = (args.database, args.run_id, args.source_id)
            if any(persistence_args) and not all(persistence_args):
                raise SystemExit(
                    "--database, --run-id, and --source-id must be provided together"
                )
            snapshot = extract_annual_financial_snapshot(
                client.get_company_facts(args.cik),
                accession_number=args.accession_number,
                period_start=args.period_start,
                period_end=args.period_end,
            )
            claim_ids: dict[str, str] = {}
            if args.database:
                claims = SqliteClaimRepository(args.database)
                for name, fact in snapshot.items():
                    claim = claims.register_xbrl_fact(
                        run_id=args.run_id,
                        source_id=args.source_id,
                        fact=fact,
                    )
                    claim_ids[name] = claim.claim_id
            print(
                json.dumps(
                    {
                        name: {
                            "concept": fact.concept,
                            "claim_id": claim_ids.get(name),
                            "period_end": fact.period_end,
                            "period_start": fact.period_start,
                            "unit": fact.unit,
                            "value": str(fact.value),
                        }
                        for name, fact in snapshot.items()
                    },
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "sec-fact":
            fact = select_filing_fact(
                client.get_company_facts(args.cik),
                taxonomy=args.taxonomy,
                concept=args.concept,
                unit=args.unit,
                accession_number=args.accession_number,
                period_end=args.period_end,
            )
            print(
                json.dumps(
                    {
                        "accession_number": fact.accession_number,
                        "concept": fact.concept,
                        "filed": fact.filed,
                        "fiscal_period": fact.fiscal_period,
                        "fiscal_year": fact.fiscal_year,
                        "form": fact.form,
                        "label": fact.label,
                        "period_end": fact.period_end,
                        "period_start": fact.period_start,
                        "taxonomy": fact.taxonomy,
                        "unit": fact.unit,
                        "value": str(fact.value),
                    },
                    sort_keys=True,
                )
            )
            return 0
        submissions = client.get_submissions(args.cik)
        filings = client.list_recent_filings(submissions, form=args.form)
        if args.command == "sec-fetch-latest":
            if bool(args.database) != bool(args.run_id):
                raise SystemExit("--database and --run-id must be provided together")
            if not filings:
                raise SystemExit(f"No {args.form} filings found for CIK {args.cik}")
            filing = filings[0]
            content = client.get_filing_document(args.cik, filing)
            artifact = LocalArtifactStore(args.artifact_root).put(content)
            source_id = None
            if args.database:
                source = SqliteSourceRepository(args.database).register(
                    run_id=args.run_id,
                    source_type="regulatory_filing",
                    title=f"{submissions.get('name', args.cik)} {filing.form}",
                    publisher="U.S. Securities and Exchange Commission",
                    canonical_url=client.filing_url(args.cik, filing),
                    source_identifier=f"SEC accession {filing.accession_number}",
                    published_at=f"{filing.filing_date}T00:00:00Z",
                    retrieved_at=datetime.now(UTC).isoformat(),
                    content_sha256=artifact.sha256,
                    size_bytes=artifact.size_bytes,
                    storage_path=str(artifact.path),
                )
                source_id = source.source_id
            value = {
                "accession_number": filing.accession_number,
                "content_sha256": artifact.sha256,
                "filing_date": filing.filing_date,
                "form": filing.form,
                "primary_document_url": client.filing_url(args.cik, filing),
                "report_date": filing.report_date,
                "size_bytes": artifact.size_bytes,
                "source_id": source_id,
                "stored_path": str(artifact.path),
            }
            print(json.dumps(value, sort_keys=True))
            return 0
        for filing in filings:
            value = {
                "accession_number": filing.accession_number,
                "form": filing.form,
                "filing_date": filing.filing_date,
                "report_date": filing.report_date,
                "primary_document_url": client.filing_url(args.cik, filing),
            }
            print(json.dumps(value, sort_keys=True))
        return 0

    if args.command == "init-db":
        upgrade_database(args.database)
        print(f"Initialized workflow database: {args.database}")
        return 0

    upgrade_database(args.database)
    repository = SqliteRunRepository(args.database)

    if args.command == "list-runs":
        runs = repository.list_runs()
        if not runs:
            print("No research runs found.")
            return 0
        print("RUN ID                                STATE        AS OF")
        for run in runs:
            print(f"{run.run_id:<36}  {run.state:<11}  {run.as_of}")
        return 0

    if args.command == "show-run":
        run = repository.get_run(args.run_id)
        claims = SqliteClaimRepository(args.database).list_for_run(run.run_id)
        analysis = SqliteAnalysisRepository(args.database).latest_for_run(run.run_id)
        memo = SqliteInvestmentMemoRepository(args.database).latest_for_run(run.run_id)
        disposition = SqliteDispositionRepository(args.database).for_run(run.run_id)
        audits = SqliteRevisionAuditRepository(args.database).list_for_run(run.run_id)
        _print_run(run, claims, analysis, audits, memo, disposition)
        return 0

    if args.command == "record-disposition":
        run = repository.get_run(args.run_id)
        if run.state is not WorkflowState.AWAITING_HUMAN_DISPOSITION:
            raise SystemExit(
                "Disposition requires a run in awaiting_human_disposition state"
            )
        event = SqliteDispositionRepository(args.database).record(
            run_id=run.run_id,
            status=args.status,
            rationale=args.rationale,
        )
        completed = repository.transition(
            run.run_id,
            expected_state=WorkflowState.AWAITING_HUMAN_DISPOSITION,
            target_state=WorkflowState.COMPLETE,
            reason="human_disposition_recorded",
        )
        print(
            json.dumps(
                {
                    "decided_at": event.decided_at,
                    "rationale": event.rationale,
                    "run_id": event.run_id,
                    "state": completed.state,
                    "status": event.status,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "import-prices":
        try:
            dataset = SqlitePriceDatasetRepository(
                args.database, args.artifact_root
            ).import_csv(
                args.csv,
                source=args.source,
                adjustment_note=args.adjustment_note,
            )
        except PriceDatasetError as error:
            raise SystemExit(str(error)) from error
        print(
            json.dumps(
                {
                    "content_sha256": dataset.content_sha256,
                    "dataset_id": dataset.dataset_id,
                    "end_date": dataset.end_date,
                    "row_count": dataset.row_count,
                    "source": dataset.source,
                    "start_date": dataset.start_date,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "screen-research":
        artifact = SqliteResearchScreener(args.database).screen(
            as_of=args.as_of,
            filters=ScreenFilters(
                min_revenue_growth=args.min_revenue_growth,
                min_operating_margin=args.min_operating_margin,
                min_net_margin=args.min_net_margin,
                min_current_ratio=args.min_current_ratio,
                min_free_cash_flow=args.min_free_cash_flow,
            ),
        )
        print(
            json.dumps(
                {
                    "as_of": artifact.as_of,
                    "filters": {
                        key: str(value) if value is not None else None
                        for key, value in asdict(artifact.filters).items()
                    },
                    "results": [asdict(item) for item in artifact.results],
                    "screen_id": artifact.screen_id,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "analyze-portfolio":
        try:
            artifact = SqlitePortfolioAnalyzer(
                args.database, args.artifact_root
            ).analyze(
                args.holdings,
                dataset_id=args.dataset,
                benchmark=args.benchmark,
                as_of=args.as_of,
            )
        except PortfolioAnalysisError as error:
            raise SystemExit(str(error)) from error
        print(
            json.dumps(
                {
                    "analysis_id": artifact.analysis_id,
                    "as_of": artifact.as_of,
                    "benchmark": artifact.benchmark,
                    "dataset_id": artifact.dataset_id,
                    "results": artifact.results,
                    "valuation_date": artifact.valuation_date,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "backtest":
        try:
            artifact = SqliteBacktester(args.database, args.artifact_root).run(
                args.dataset,
                ticker=args.ticker,
                benchmark=args.benchmark,
                short_window=args.short_window,
                long_window=args.long_window,
                initial_cash=args.initial_cash,
                transaction_cost_bps=args.transaction_cost_bps,
            )
        except BacktestError as error:
            raise SystemExit(str(error)) from error
        print(
            json.dumps(
                {
                    "backtest_id": artifact.backtest_id,
                    "benchmark": artifact.benchmark,
                    "dataset_id": artifact.dataset_id,
                    "parameters": artifact.parameters,
                    "results": artifact.results,
                    "strategy": artifact.strategy,
                    "strategy_version": artifact.strategy_version,
                    "ticker": artifact.ticker,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "create-monitor":
        try:
            monitor = SqliteDecisionMonitoring(
                args.database, args.artifact_root
            ).create_monitor(run_id=args.run_id, name=args.name, rules_path=args.rules)
        except MonitoringError as error:
            raise SystemExit(str(error)) from error
        print(
            json.dumps(
                {
                    "monitor_id": monitor.monitor_id,
                    "name": monitor.name,
                    "rules": [
                        {
                            "rule_id": rule.rule_id,
                            "threshold": str(rule.threshold),
                            "ticker": rule.ticker,
                            "type": rule.type,
                        }
                        for rule in monitor.rules
                    ],
                    "rules_sha256": monitor.rules_sha256,
                    "run_id": monitor.run_id,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "evaluate-monitor":
        try:
            evaluation = SqliteDecisionMonitoring(
                args.database, args.artifact_root
            ).evaluate(args.monitor_id, dataset_id=args.dataset, as_of=args.as_of)
        except MonitoringError as error:
            raise SystemExit(str(error)) from error
        print(
            json.dumps(
                {
                    "as_of": evaluation.as_of,
                    "dataset_id": evaluation.dataset_id,
                    "dataset_sha256": evaluation.dataset_sha256,
                    "evaluation_id": evaluation.evaluation_id,
                    "monitor_id": evaluation.monitor_id,
                    "results": evaluation.results,
                },
                sort_keys=True,
            )
        )
        return 0

    if args.command == "list-alerts":
        try:
            alerts = SqliteDecisionMonitoring(
                args.database, args.artifact_root
            ).list_alerts(monitor_id=args.monitor, status=args.status)
        except MonitoringError as error:
            raise SystemExit(str(error)) from error
        print(json.dumps([asdict(alert) for alert in alerts], sort_keys=True))
        return 0

    if args.command == "acknowledge-alert":
        try:
            acknowledgement = SqliteDecisionMonitoring(
                args.database, args.artifact_root
            ).acknowledge(args.alert_id, note=args.note)
        except MonitoringError as error:
            raise SystemExit(str(error)) from error
        print(json.dumps(asdict(acknowledgement), sort_keys=True))
        return 0

    if args.command == "compare-research":
        try:
            review = SqliteResearchReviewRepository(args.database).compare(
                args.baseline_run_id, args.current_run_id
            )
        except ResearchReviewError as error:
            raise SystemExit(str(error)) from error
        print(json.dumps(_review_dict(review), sort_keys=True))
        return 0

    if args.command == "show-research-review":
        repository = SqliteResearchReviewRepository(args.database)
        try:
            review = repository.get(args.review_id)
        except ResearchReviewError as error:
            raise SystemExit(str(error)) from error
        value = _review_dict(review)
        outcome = repository.outcome_for_review(review.review_id)
        value["human_outcome"] = asdict(outcome) if outcome is not None else None
        print(json.dumps(value, sort_keys=True))
        return 0

    if args.command == "record-review-outcome":
        try:
            outcome = SqliteResearchReviewRepository(args.database).record_outcome(
                args.review_id,
                outcome=args.outcome,
                rationale=args.rationale,
            )
        except ResearchReviewError as error:
            raise SystemExit(str(error)) from error
        print(json.dumps(asdict(outcome), sort_keys=True))
        return 0

    if args.command == "create-run":
        run = repository.create_run(memo_id=args.memo_id, as_of=args.as_of)
        print(json.dumps(_run_dict(run), sort_keys=True))
        return 0

    if args.command == "transition":
        run = repository.transition(
            args.run_id,
            expected_state=args.expected_state,
            target_state=args.target_state,
            reason=args.reason,
        )
        print(json.dumps(_run_dict(run), sort_keys=True))
        return 0

    if args.command == "analyze-financials":
        claims = SqliteClaimRepository(args.database).list_for_run(args.run_id)
        try:
            generated = OpenAIFinancialAnalysisAdapter().analyze(
                question=args.question,
                claims=claims,
            )
        except AnalysisGenerationError as error:
            raise SystemExit(str(error)) from error
        artifact = SqliteAnalysisRepository(
            args.database
        ).save_openai_financial_analysis(
            run_id=args.run_id,
            generated=generated,
        )
        print(
            json.dumps(
                {
                    "analysis": artifact.analysis.model_dump(),
                    "artifact_id": artifact.artifact_id,
                    "input_claim_ids": artifact.input_claim_ids,
                    "evidence_gaps": artifact.evidence_gaps,
                    "model": artifact.model,
                    "prompt_version": artifact.prompt_version,
                    "provider_response_id": artifact.provider_response_id,
                    "schema_version": artifact.schema_version,
                },
                sort_keys=True,
            )
        )
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


def _run_dict(run: object) -> dict[str, str]:
    return {
        "run_id": run.run_id,
        "memo_id": run.memo_id,
        "workflow_version": run.workflow_version,
        "state": run.state,
        "as_of": run.as_of,
        "created_at": run.created_at,
        "updated_at": run.updated_at,
    }


def _review_dict(review: object) -> dict:
    return {
        "baseline_memo_id": review.baseline_memo_id,
        "baseline_run_id": review.baseline_run_id,
        "content": review.content,
        "created_at": review.created_at,
        "current_memo_id": review.current_memo_id,
        "current_run_id": review.current_run_id,
        "review_id": review.review_id,
        "ticker": review.ticker,
    }


def _print_run(
    run: object,
    claims: list[object],
    artifact: object | None,
    audits: list[object],
    memo: object | None,
    disposition: object | None,
) -> None:
    print(f"Run: {run.run_id}")
    print(f"State: {run.state}")
    print(f"As of: {run.as_of}")
    print(f"Claims: {len(claims)}")
    for claim in claims:
        print(f"  - [{claim.claim_id}] {claim.statement}")
    print(f"Cross-filing revision audits: {len(audits)}")
    for audit in audits:
        revision = audit.revision
        print(
            f"  - {revision.concept} {revision.period_end}: "
            f"{revision.original_value} ({revision.original_accession}) -> "
            f"{revision.later_value} ({revision.later_accession}); "
            f"classification={revision.classification}"
        )
    if memo is None:
        print("Investment memo: not available")
    else:
        print(f"Investment memo: {memo.artifact_id}")
    if disposition is None:
        print("Recorded human disposition: undecided")
    else:
        print(f"Recorded human disposition: {disposition.status}")
        if disposition.rationale:
            print(f"Disposition rationale: {disposition.rationale}")
    if artifact is None:
        print("Analysis: not available")
        return
    print(f"Analysis: {artifact.analysis.assessment}")
    print(f"Model: {artifact.model} (prompt {artifact.prompt_version})")
    print(
        "Model usage: "
        f"input_tokens={artifact.input_tokens}, "
        f"output_tokens={artifact.output_tokens}, "
        f"request_duration_ms={artifact.request_duration_ms}"
    )
    print(f"Summary: {artifact.analysis.summary}")
    for title, points in (
        ("Strengths", artifact.analysis.strengths),
        ("Concerns", artifact.analysis.concerns),
        ("Uncertainties", artifact.analysis.uncertainties),
        ("Cash allocation", artifact.analysis.cash_allocation),
        ("Trends", artifact.analysis.trends),
        ("Business quality", artifact.analysis.business_quality),
        ("Material risks", artifact.analysis.material_risks),
        ("Bull case", artifact.analysis.bull_case),
        ("Base case", artifact.analysis.base_case),
        ("Bear case", artifact.analysis.bear_case),
        ("Devil's advocate", artifact.analysis.devils_advocate),
        ("Valuation scenarios", artifact.analysis.valuation),
    ):
        print(f"{title}:")
        for point in points:
            print(f"  - {point.text}")
    print("Known limitations:")
    if artifact.analysis.known_limitations:
        for limitation in artifact.analysis.known_limitations:
            print(f"  - {limitation}")
    else:
        print("  - No known evidence gaps were recorded.")
