#!/usr/bin/env python3
"""
0003_audit_sessions.py --- audit sessions

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-12
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE TABLE audit_sessions (
            session_id UUID PRIMARY KEY,
            trace_id VARCHAR(64) NOT NULL UNIQUE,
            tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            ended_at TIMESTAMPTZ
        )
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP TABLE IF EXISTS audit_sessions
        """
    )
