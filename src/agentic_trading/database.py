"""Shared SQLAlchemy database configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy import URL, Engine, create_engine, event


def create_sqlite_engine(database_path: Path) -> Engine:
    """Create a SQLite engine with foreign-key enforcement enabled."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(URL.create("sqlite", database=str(database_path)))

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection: Any, _: object) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()

    return engine
