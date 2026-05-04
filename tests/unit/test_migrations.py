#!/usr/bin/env python3
"""
test_migrations.py --- structural tests over the Alembic migration files

Contains:
    migration_files(): returns all migration files sorted by revision number
    test_every_migration_has_revision_linkage(): verifies revision declarations
"""

import re
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parents[2] / "infra" / "migrations" / "versions"


def migration_files() -> list[Path]:
    """Returns all migration files sorted by revision number.

    Returns:
        paths: Migration file paths sorted lexically by revision.
    """
    return sorted(MIGRATIONS_DIR.glob("*.py"))


def test_every_migration_has_revision_linkage() -> None:
    """Verifies each migration declares revision linkage."""
    for path in migration_files():
        content = path.read_text()
        assert 'revision = "' in content, path.name
        assert "down_revision" in content, path.name
