#!/usr/bin/env python3
"""
0008_outbox_events.py --- outbox events

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-02
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE TABLE outbox_events (
            outbox_id UUID PRIMARY KEY,
            trace_id VARCHAR(64) NOT NULL,
            topic VARCHAR(64) NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}',
            published_at TIMESTAMPTZ,
            attempts INTEGER NOT NULL DEFAULT 0
        )
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP TABLE outbox_events
        """
    )
