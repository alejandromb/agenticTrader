"""Command-line interface for local Agentic Trading workflows."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv

from agentic_trading.analysis_repository import SqliteAnalysisRepository
from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.claim_repository import SqliteClaimRepository
from agentic_trading.financials import extract_annual_financial_snapshot
from agentic_trading.migrations import upgrade_database
from agentic_trading.openai_adapter import (
    AnalysisGenerationError,
    OpenAIFinancialAnalysisAdapter,
)
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.research import CompanyResearchService
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
        "research-company", help="run the complete version-one research workflow"
    )
    research.add_argument("ticker")
    research.add_argument("--question", required=True)
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
            ).research(ticker=args.ticker.upper(), question=args.question)
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
                    "model": result.analysis.model,
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
        _print_run(run, claims, analysis)
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


def _print_run(run: object, claims: list[object], artifact: object | None) -> None:
    print(f"Run: {run.run_id}")
    print(f"State: {run.state}")
    print(f"As of: {run.as_of}")
    print(f"Claims: {len(claims)}")
    for claim in claims:
        print(f"  - [{claim.claim_id}] {claim.statement}")
    if artifact is None:
        print("Analysis: not available")
        return
    print(f"Analysis: {artifact.analysis.assessment}")
    print(f"Model: {artifact.model} (prompt {artifact.prompt_version})")
    print(f"Summary: {artifact.analysis.summary}")
    for title, points in (
        ("Strengths", artifact.analysis.strengths),
        ("Concerns", artifact.analysis.concerns),
        ("Uncertainties", artifact.analysis.uncertainties),
        ("Cash allocation", artifact.analysis.cash_allocation),
    ):
        print(f"{title}:")
        for point in points:
            print(f"  - {point.text}")
