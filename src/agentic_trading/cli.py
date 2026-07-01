"""Command-line interface for local Agentic Trading workflows."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.claim_repository import SqliteClaimRepository
from agentic_trading.financials import extract_annual_financial_snapshot
from agentic_trading.migrations import upgrade_database
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.sec import SecClient
from agentic_trading.source_repository import SqliteSourceRepository
from agentic_trading.validation import validate_memo_files
from agentic_trading.workflow import WorkflowState
from agentic_trading.xbrl import select_filing_fact

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

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "validate-memo":
        validate_memo_files(args.memo, args.schema)
        print(f"Valid investment memo: {args.memo}")
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

    repository = SqliteRunRepository(args.database)
    repository.initialize()

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
