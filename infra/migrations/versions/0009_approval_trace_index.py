#!/usr/bin/env python3
"""
0009_approval_trace_index.py --- approval trace index

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-05
"""

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE INDEX ix_approval_trace ON approval_requests (trace_id)
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP INDEX ix_approval_trace
        """
    )
