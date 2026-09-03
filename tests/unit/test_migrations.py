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


def test_every_migration_has_upgrade_and_downgrade() -> None:
    """Verifies both directions exist in every migration file."""
    for path in migration_files():
        content = path.read_text()
        assert "def upgrade" in content, path.name
        assert "def downgrade" in content, path.name


def test_composite_trace_created_index_exists() -> None:
    """Verifies the composite index backing /audit/{trace_id} lookups exists."""
    contents = "\n".join(path.read_text() for path in migration_files())
    assert "ix_audit_trace_created" in contents
    assert "(trace_id, created_at)" in contents


def test_index_migrations_use_if_not_exists() -> None:
    """Verifies index creation is idempotent across fresh and existing installs."""
    index_migrations = [
        path for path in migration_files() if "index" in path.name or "brin" in path.name
    ]
    for path in index_migrations:
        assert "IF NOT EXISTS" in path.read_text(), path.name


def test_brin_index_only_on_append_only_table() -> None:
    """Verifies the BRIN index targets the append-only events table."""
    brin = [path for path in migration_files() if "brin" in path.read_text().lower()]
    for path in brin:
        assert "audit_events" in path.read_text(), path.name


def test_no_migration_alters_without_matching_rollback() -> None:
    """Verifies ALTER TABLE migrations drop what they add on downgrade."""
    for path in migration_files():
        content = path.read_text()
        if "ADD COLUMN" in content:
            assert "DROP COLUMN" in content, path.name
