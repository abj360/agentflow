#!/usr/bin/env python3
"""
0001_audit_events.py --- audit events

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0001
Revises: None
Create Date: 2026-05-01
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE TABLE audit_events (
            event_id UUID PRIMARY KEY,
            trace_id VARCHAR(64) NOT NULL,
            kind VARCHAR(32) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            prev_hash VARCHAR(64) NOT NULL,
            event_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP TABLE audit_events
        """
    )
