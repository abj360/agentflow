#!/usr/bin/env python3
"""
0007_composite_trace_created.py --- composite trace created

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-27
"""

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE INDEX ix_audit_trace_created ON audit_events (trace_id, created_at)
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP INDEX ix_audit_trace_created
        """
    )
