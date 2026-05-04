#!/usr/bin/env python3
"""
0002_trace_id_and_created_at_indexes.py --- trace id and created at indexes

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-04
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_events_trace_id ON audit_events (trace_id)
        CREATE INDEX IF NOT EXISTS ix_audit_events_created_at ON audit_events (created_at)
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP INDEX ix_audit_events_created_at
        DROP INDEX ix_audit_events_trace_id
        """
    )
