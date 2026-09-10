"""Programmatic database migration entry points."""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import URL


def upgrade_database(database_path: Path, revision: str = "head") -> None:
    """Upgrade a SQLite database to an Alembic revision."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
    project_root = Path(__file__).parents[2]
    bundled_root = Path(__file__).parent / "_resources"
    if bundled_root.is_dir():
        project_root = bundled_root
    config = Config(project_root / "alembic.ini")
    config.set_main_option("script_location", str(project_root / "migrations"))
    url = URL.create("sqlite", database=str(database_path))
    config.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False))
    command.upgrade(config, revision)
