#!/usr/bin/env python3
"""
0005_approval_requests.py --- approval requests

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-23
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE TABLE approval_requests (
            approval_id UUID PRIMARY KEY,
            trace_id VARCHAR(64) NOT NULL,
            tool_name VARCHAR(128) NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP TABLE approval_requests
        """
    )
