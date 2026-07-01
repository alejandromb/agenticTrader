from __future__ import annotations

from pathlib import Path

import pytest

from agentic_trading.artifacts import LocalArtifactStore


def test_artifact_round_trip_is_content_addressed(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path)

    first = store.put(b"filing content")
    second = store.put(b"filing content")

    assert first == second
    assert first.size_bytes == 14
    assert first.path.exists()
    assert store.get(first.sha256) == b"filing content"


def test_invalid_digest_is_rejected(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path)

    with pytest.raises(ValueError, match="SHA-256"):
        store.get("../not-a-digest")


def test_corrupted_artifact_is_detected(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path)
    artifact = store.put(b"original")
    artifact.path.write_bytes(b"tampered")

    with pytest.raises(ValueError, match="hash mismatch"):
        store.get(artifact.sha256)
