#!/usr/bin/env python3
"""
0015_sessions_started_at_index.py --- sessions started at index

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0015
Revises: 0014
Create Date: 2026-07-05
"""

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_sessions_started_at ON audit_sessions (started_at)
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP INDEX ix_audit_sessions_started_at
        """
    )
