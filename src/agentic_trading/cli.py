"""Command-line interface for local Agentic Trading workflows."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from pathlib import Path

from agentic_trading.artifacts import LocalArtifactStore
from agentic_trading.repository import SqliteRunRepository
from agentic_trading.sec import SecClient
from agentic_trading.validation import validate_memo_files
from agentic_trading.workflow import WorkflowState

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

    if args.command in {"sec-filings", "sec-fetch-latest"}:
        user_agent = os.environ.get("SEC_USER_AGENT")
        if not user_agent:
            raise SystemExit(
                "SEC_USER_AGENT is required and must identify the application owner"
            )
        client = SecClient(user_agent)
        submissions = client.get_submissions(args.cik)
        filings = client.list_recent_filings(submissions, form=args.form)
        if args.command == "sec-fetch-latest":
            if not filings:
                raise SystemExit(f"No {args.form} filings found for CIK {args.cik}")
            filing = filings[0]
            content = client.get_filing_document(args.cik, filing)
            artifact = LocalArtifactStore(args.artifact_root).put(content)
            value = {
                "accession_number": filing.accession_number,
                "content_sha256": artifact.sha256,
                "filing_date": filing.filing_date,
                "form": filing.form,
                "primary_document_url": client.filing_url(args.cik, filing),
                "report_date": filing.report_date,
                "size_bytes": artifact.size_bytes,
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

    repository = SqliteRunRepository(args.database)
    repository.initialize()

    if args.command == "init-db":
        print(f"Initialized workflow database: {args.database}")
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
