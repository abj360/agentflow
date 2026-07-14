#!/usr/bin/env python3
"""
0017_checksum_index.py --- checksum index

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-14
"""

from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_events_checksum ON audit_events (checksum)
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP INDEX ix_audit_events_checksum
        """
    )
