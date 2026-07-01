"""Validation for canonical investment memo artifacts."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


class MemoValidationError(ValueError):
    """Raised when a memo violates structural or semantic rules."""


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from *path*."""
    with path.open(encoding="utf-8") as file:
        value = json.load(file)
    if not isinstance(value, dict):
        raise MemoValidationError(f"Expected a JSON object in {path}")
    return value


def validate_memo(memo: dict[str, Any], schema: dict[str, Any]) -> None:
    """Validate a memo against its schema and cross-reference invariants."""
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(memo), key=lambda error: list(error.path))
    messages = [_format_schema_error(error) for error in errors]
    messages.extend(_semantic_errors(memo))
    if messages:
        details = "\n- ".join(messages)
        raise MemoValidationError(f"Investment memo is invalid:\n- {details}")


def validate_memo_files(memo_path: Path, schema_path: Path) -> None:
    """Load and validate a memo and schema from disk."""
    validate_memo(load_json(memo_path), load_json(schema_path))


def _format_schema_error(error: Any) -> str:
    location = ".".join(str(part) for part in error.absolute_path) or "<root>"
    return f"{location}: {error.message}"


def _semantic_errors(memo: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    claims = memo.get("claims", [])
    evidence = memo.get("evidence", [])

    claim_ids = [claim.get("claim_id") for claim in claims]
    evidence_ids = [item.get("evidence_id") for item in evidence]
    errors.extend(_duplicate_errors("claim", claim_ids))
    errors.extend(_duplicate_errors("evidence", evidence_ids))

    known_claims = set(claim_ids)
    known_evidence = set(evidence_ids)

    for claim in claims:
        claim_id = claim.get("claim_id", "<unknown>")
        for evidence_id in claim.get("evidence_ids", []):
            if evidence_id not in known_evidence:
                errors.append(f"{claim_id} references unknown evidence {evidence_id}")
        for input_id in claim.get("input_claim_ids", []):
            if input_id not in known_claims:
                errors.append(f"{claim_id} references unknown input claim {input_id}")
            if input_id == claim_id:
                errors.append(f"{claim_id} cannot use itself as an input")

    referenced_claims = _referenced_section_claims(memo)
    for claim_id in referenced_claims:
        if claim_id not in known_claims:
            errors.append(f"memo section references unknown claim {claim_id}")

    as_of = _parse_datetime(memo.get("as_of"))
    if as_of is not None:
        for item in evidence:
            published_at = _parse_datetime(item.get("published_at"))
            if published_at is not None and published_at > as_of:
                errors.append(
                    f"{item.get('evidence_id', '<unknown>')} was published after as_of"
                )

    return errors


def _duplicate_errors(kind: str, identifiers: list[Any]) -> list[str]:
    seen: set[Any] = set()
    duplicates: set[Any] = set()
    for identifier in identifiers:
        if identifier in seen:
            duplicates.add(identifier)
        seen.add(identifier)
    return [f"duplicate {kind} ID {identifier}" for identifier in sorted(duplicates)]


def _referenced_section_claims(memo: dict[str, Any]) -> list[str]:
    references = list(memo.get("executive_view", {}).get("claim_ids", []))
    for section in memo.get("sections", {}).values():
        references.extend(section.get("claim_ids", []))
    return references


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
