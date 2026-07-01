"""Content-addressed local artifact storage."""

from __future__ import annotations

import hashlib
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class StoredArtifact:
    sha256: str
    size_bytes: int
    path: Path


class LocalArtifactStore:
    """Store immutable bytes by SHA-256 digest under a configured root."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def put(self, content: bytes) -> StoredArtifact:
        """Persist bytes atomically and return their stable identity."""
        digest = hashlib.sha256(content).hexdigest()
        destination = self._root / "sha256" / digest[:2] / digest
        destination.parent.mkdir(parents=True, exist_ok=True)

        if not destination.exists():
            temporary_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    dir=destination.parent, delete=False
                ) as temporary:
                    temporary.write(content)
                    temporary.flush()
                    os.fsync(temporary.fileno())
                    temporary_path = Path(temporary.name)
                temporary_path.replace(destination)
            finally:
                if temporary_path is not None:
                    temporary_path.unlink(missing_ok=True)

        return StoredArtifact(
            sha256=digest,
            size_bytes=len(content),
            path=destination,
        )

    def get(self, sha256: str) -> bytes:
        """Read and verify an artifact by digest."""
        _validate_digest(sha256)
        path = self._root / "sha256" / sha256[:2] / sha256
        content = path.read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        if actual != sha256:
            raise ValueError(
                f"Artifact hash mismatch: expected {sha256}, found {actual}"
            )
        return content


def _validate_digest(value: str) -> None:
    if len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ValueError("Expected a lowercase SHA-256 digest")
