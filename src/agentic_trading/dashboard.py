"""Loopback-only HTTP dashboard over the existing research services."""

from __future__ import annotations

import ipaddress
import json
import os
import re
import secrets
from collections.abc import Callable
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import TCPServer
from typing import Any
from urllib.parse import unquote, urlparse

from agentic_trading.analysis_repository import SqliteAnalysisRepository
from agentic_trading.disposition_repository import (
    ALLOWED_DISPOSITIONS,
    SqliteDispositionRepository,
)
from agentic_trading.memo_repository import SqliteInvestmentMemoRepository
from agentic_trading.migrations import upgrade_database
from agentic_trading.openai_adapter import (
    AnalysisGenerationError,
    OpenAIFinancialAnalysisAdapter,
)
from agentic_trading.repository import RunNotFoundError, SqliteRunRepository
from agentic_trading.research import CompanyResearchService
from agentic_trading.revision_repository import SqliteRevisionAuditRepository
from agentic_trading.sec import SecClient, SecClientError
from agentic_trading.workflow import WorkflowState
from agentic_trading.xbrl import XbrlFactError

_ASSETS = Path(__file__).parent / "dashboard_assets"
_TICKER = re.compile(r"^[A-Z][A-Z0-9.-]{0,9}$")
_MAX_BODY = 64 * 1024


class DashboardError(ValueError):
    pass


class LoopbackDashboardServer(ThreadingHTTPServer):
    """Avoid reverse-DNS lookup while binding the already-validated host."""

    def server_bind(self) -> None:
        TCPServer.server_bind(self)
        host, port = self.server_address[:2]
        self.server_name = host
        self.server_port = port


class DashboardDataService:
    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._runs = SqliteRunRepository(database_path)
        self._memos = SqliteInvestmentMemoRepository(database_path)
        self._analysis = SqliteAnalysisRepository(database_path)
        self._dispositions = SqliteDispositionRepository(database_path)
        self._audits = SqliteRevisionAuditRepository(database_path)

    def list_runs(self) -> list[dict[str, Any]]:
        values = []
        for run in self._runs.list_runs():
            memo = self._memos.latest_for_run(run.run_id)
            disposition = self._dispositions.for_run(run.run_id)
            subject = memo.memo.get("subject", {}) if memo is not None else {}
            values.append(
                {
                    "run_id": run.run_id,
                    "state": run.state.value,
                    "as_of": run.as_of,
                    "created_at": run.created_at,
                    "ticker": subject.get("ticker"),
                    "company_name": subject.get("company_name"),
                    "memo_available": memo is not None,
                    "disposition": disposition.status if disposition else None,
                }
            )
        return values

    def run_detail(self, run_id: str) -> dict[str, Any]:
        run = self._runs.get_run(run_id)
        memo = self._memos.latest_for_run(run_id)
        analysis = self._analysis.latest_for_run(run_id)
        disposition = self._dispositions.for_run(run_id)
        audits = self._audits.list_for_run(run_id)
        return {
            "run": {
                "run_id": run.run_id,
                "state": run.state.value,
                "as_of": run.as_of,
                "created_at": run.created_at,
                "updated_at": run.updated_at,
            },
            "memo": memo.memo if memo is not None else None,
            "memo_artifact_id": memo.artifact_id if memo is not None else None,
            "analysis": (
                analysis.analysis.model_dump(mode="json")
                if analysis is not None
                else None
            ),
            "analysis_metadata": (
                {
                    "artifact_id": analysis.artifact_id,
                    "model": analysis.model,
                    "prompt_version": analysis.prompt_version,
                    "evidence_gaps": analysis.evidence_gaps,
                    "input_tokens": analysis.input_tokens,
                    "output_tokens": analysis.output_tokens,
                    "request_duration_ms": analysis.request_duration_ms,
                }
                if analysis is not None
                else None
            ),
            "disposition": asdict(disposition) if disposition is not None else None,
            "revision_audits": [
                {
                    "audit_id": audit.audit_id,
                    "concept": audit.revision.concept,
                    "period_end": audit.revision.period_end,
                    "original_value": str(audit.revision.original_value),
                    "later_value": str(audit.revision.later_value),
                    "classification": audit.revision.classification,
                }
                for audit in audits
            ],
            "can_record_disposition": (
                run.state == WorkflowState.AWAITING_HUMAN_DISPOSITION
                and disposition is None
            ),
        }

    def record_disposition(
        self, run_id: str, *, status: str, rationale: str
    ) -> dict[str, Any]:
        if status not in ALLOWED_DISPOSITIONS:
            raise DashboardError(f"Invalid disposition: {status}")
        rationale = rationale.strip()
        if not rationale:
            raise DashboardError("Disposition rationale is required")
        if len(rationale) > 2_000:
            raise DashboardError("Disposition rationale is too long")
        run = self._runs.get_run(run_id)
        if run.state != WorkflowState.AWAITING_HUMAN_DISPOSITION:
            raise DashboardError("Run is not awaiting human disposition")
        if self._dispositions.for_run(run_id) is not None:
            raise DashboardError("Run already has a human disposition")
        event = self._dispositions.record(
            run_id=run_id, status=status, rationale=rationale
        )
        completed = self._runs.transition(
            run_id,
            expected_state=WorkflowState.AWAITING_HUMAN_DISPOSITION,
            target_state=WorkflowState.COMPLETE,
            reason="human_disposition_recorded_from_dashboard",
        )
        return {"event": asdict(event), "state": completed.state.value}


def _default_research_runner(
    database_path: Path, artifact_root: Path
) -> Callable[[str, str], dict[str, Any]]:
    def run(ticker: str, question: str) -> dict[str, Any]:
        user_agent = os.environ.get("SEC_USER_AGENT")
        if not user_agent:
            raise DashboardError("SEC_USER_AGENT is not configured")
        if not os.environ.get("OPENAI_API_KEY"):
            raise DashboardError("OPENAI_API_KEY is not configured")
        result = CompanyResearchService(
            database_path=database_path,
            artifact_root=artifact_root,
            sec_client=SecClient(user_agent),
            analysis_adapter=OpenAIFinancialAnalysisAdapter(),
        ).research(ticker=ticker, question=question)
        return {
            "run_id": result.run.run_id,
            "state": result.run.state.value,
            "ticker": result.company.ticker,
            "company": result.company.name,
            "memo_artifact_id": result.memo.artifact_id,
        }

    return run


def create_dashboard_server(
    *,
    host: str,
    port: int,
    database_path: Path,
    artifact_root: Path,
    research_runner: Callable[[str, str], dict[str, Any]] | None = None,
) -> LoopbackDashboardServer:
    _validate_loopback(host)
    if not 0 <= port <= 65535:
        raise DashboardError("Port must be between 0 and 65535")
    upgrade_database(database_path)
    token = secrets.token_urlsafe(32)
    data = DashboardDataService(database_path)
    run_research = research_runner or _default_research_runner(
        database_path, artifact_root
    )

    class DashboardHandler(BaseHTTPRequestHandler):
        server_version = "AgenticTradingDashboard/1.0"

        def do_GET(self) -> None:  # noqa: N802
            path = unquote(urlparse(self.path).path)
            if path == "/":
                self._asset("index.html", "text/html; charset=utf-8")
                return
            if path == "/app.css":
                self._asset("app.css", "text/css; charset=utf-8")
                return
            if path == "/app.js":
                self._asset("app.js", "text/javascript; charset=utf-8")
                return
            if path == "/api/config":
                self._json(
                    {
                        "csrf_token": token,
                        "openai_configured": bool(os.environ.get("OPENAI_API_KEY")),
                        "sec_configured": bool(os.environ.get("SEC_USER_AGENT")),
                    }
                )
                return
            if path == "/api/runs":
                self._json({"runs": data.list_runs()})
                return
            prefix = "/api/runs/"
            if path.startswith(prefix) and path.count("/") == 3:
                try:
                    self._json(data.run_detail(path.removeprefix(prefix)))
                except RunNotFoundError:
                    self._error(HTTPStatus.NOT_FOUND, "Research run not found")
                return
            self._error(HTTPStatus.NOT_FOUND, "Not found")

        def do_POST(self) -> None:  # noqa: N802
            if self.headers.get("X-Agentic-CSRF") != token:
                self._error(HTTPStatus.FORBIDDEN, "Invalid request token")
                return
            try:
                payload = self._read_json()
            except DashboardError as error:
                self._error(HTTPStatus.BAD_REQUEST, str(error))
                return
            path = unquote(urlparse(self.path).path)
            if path == "/api/research":
                self._research(payload)
                return
            suffix = "/disposition"
            if path.startswith("/api/runs/") and path.endswith(suffix):
                run_id = path.removeprefix("/api/runs/").removesuffix(suffix)
                try:
                    result = data.record_disposition(
                        run_id,
                        status=_string(payload, "status"),
                        rationale=_string(payload, "rationale"),
                    )
                except RunNotFoundError:
                    self._error(HTTPStatus.NOT_FOUND, "Research run not found")
                    return
                except (DashboardError, ValueError) as error:
                    self._error(HTTPStatus.CONFLICT, str(error))
                    return
                self._json(result, status=HTTPStatus.CREATED)
                return
            self._error(HTTPStatus.NOT_FOUND, "Not found")

        def _research(self, payload: dict[str, Any]) -> None:
            try:
                ticker = _string(payload, "ticker").strip().upper()
                question = _string(payload, "question").strip()
                if not _TICKER.fullmatch(ticker):
                    raise DashboardError("Ticker format is invalid")
                if not question:
                    raise DashboardError("Research question is required")
                if len(question) > 4_000:
                    raise DashboardError("Research question is too long")
                result = run_research(ticker, question)
            except (
                AnalysisGenerationError,
                DashboardError,
                SecClientError,
                ValueError,
                XbrlFactError,
            ) as error:
                self._error(HTTPStatus.BAD_REQUEST, str(error))
                return
            self._json(result, status=HTTPStatus.CREATED)

        def _read_json(self) -> dict[str, Any]:
            if self.headers.get_content_type() != "application/json":
                raise DashboardError("Content-Type must be application/json")
            try:
                length = int(self.headers.get("Content-Length", ""))
            except ValueError as error:
                raise DashboardError("Content-Length is invalid") from error
            if not 0 < length <= _MAX_BODY:
                raise DashboardError("Request body size is invalid")
            try:
                value = json.loads(self.rfile.read(length))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise DashboardError("Request body must be valid JSON") from error
            if not isinstance(value, dict):
                raise DashboardError("Request body must be a JSON object")
            return value

        def _asset(self, name: str, content_type: str) -> None:
            payload = (_ASSETS / name).read_bytes()
            self.send_response(HTTPStatus.OK)
            self._security_headers(content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, value: Any, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            payload = json.dumps(value, sort_keys=True).encode()
            self.send_response(status)
            self._security_headers("application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def _error(self, status: HTTPStatus, message: str) -> None:
            self._json({"error": message}, status=status)

        def _security_headers(self, content_type: str) -> None:
            self.send_header("Content-Type", content_type)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self'; style-src 'self'; "
                "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
            )

        def log_message(self, format: str, *args: object) -> None:
            return

    return LoopbackDashboardServer((host, port), DashboardHandler)


def serve_dashboard(
    *, host: str, port: int, database_path: Path, artifact_root: Path
) -> None:
    server = create_dashboard_server(
        host=host,
        port=port,
        database_path=database_path,
        artifact_root=artifact_root,
    )
    address, assigned_port = server.server_address
    print(f"Agentic Trading dashboard: http://{address}:{assigned_port}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def _validate_loopback(host: str) -> None:
    try:
        addresses = {
            item[4][0] for item in __import__("socket").getaddrinfo(host, None)
        }
        if not addresses or not all(
            ipaddress.ip_address(item).is_loopback for item in addresses
        ):
            raise DashboardError(
                "Dashboard host must resolve only to loopback addresses"
            )
    except OSError as error:
        raise DashboardError(f"Dashboard host cannot be resolved: {host}") from error


def _string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise DashboardError(f"{key} must be a string")
    return value
