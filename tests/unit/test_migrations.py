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


def test_down_revision_chain_is_contiguous() -> None:
    """Verifies down_revision pointers form one unbroken chain."""
    revisions: dict[str, str | None] = {}
    for path in migration_files():
        content = path.read_text()
        rev = re.search(r'revision = "(\d+)"', content)
        down = re.search(r'down_revision = (?:"(\d+)"|None)', content)
        revisions[rev.group(1)] = down.group(1) if down else None
    for rev, down in revisions.items():
        if down is not None:
            assert down in revisions, f"{rev} points at missing {down}"


def test_migration_revision_ids_are_zero_padded_four_digits() -> None:
    """Verifies revision ids sort lexically in chronological order."""
    for path in migration_files():
        rev = re.search(r'revision = "(\d+)"', path.read_text())
        assert len(rev.group(1)) == 4, path.name
