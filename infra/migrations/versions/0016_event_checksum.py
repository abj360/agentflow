#!/usr/bin/env python3
"""
0016_event_checksum.py --- event checksum

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-11
"""

from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        ALTER TABLE audit_events ADD COLUMN checksum VARCHAR(64)
        """
    )
    op.execute("COMMENT ON COLUMN audit_events.checksum IS 'sha256 of canonical payload'")


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        ALTER TABLE audit_events DROP COLUMN checksum
        """
    )
