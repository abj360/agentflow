#!/usr/bin/env python3
"""
0011_created_at_brin.py --- created at brin

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-15
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_events_created_brin ON audit_events USING brin (created_at)
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP INDEX ix_audit_events_created_brin
        """
    )
