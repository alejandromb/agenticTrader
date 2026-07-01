from __future__ import annotations

import copy
from pathlib import Path

import pytest

from agentic_trading.validation import MemoValidationError, load_json, validate_memo

ROOT = Path(__file__).parents[1]
SCHEMA = load_json(ROOT / "schemas/investment-memo-v1.schema.json")
EXAMPLE = load_json(ROOT / "examples/investment-memos/aapl-2025-example.json")


def test_example_memo_is_valid() -> None:
    validate_memo(EXAMPLE, SCHEMA)


def test_unknown_evidence_reference_is_rejected() -> None:
    memo = copy.deepcopy(EXAMPLE)
    memo["claims"][0]["evidence_ids"] = ["missing-evidence"]

    with pytest.raises(MemoValidationError, match="unknown evidence"):
        validate_memo(memo, SCHEMA)


def test_evidence_after_as_of_is_rejected() -> None:
    memo = copy.deepcopy(EXAMPLE)
    memo["evidence"][0]["published_at"] = "2025-11-01T00:00:00Z"

    with pytest.raises(MemoValidationError, match="published after as_of"):
        validate_memo(memo, SCHEMA)


def test_duplicate_claim_id_is_rejected() -> None:
    memo = copy.deepcopy(EXAMPLE)
    memo["claims"][1]["claim_id"] = memo["claims"][0]["claim_id"]

    with pytest.raises(MemoValidationError, match="duplicate claim ID"):
        validate_memo(memo, SCHEMA)
