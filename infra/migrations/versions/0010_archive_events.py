#!/usr/bin/env python3
"""
0010_archive_events.py --- archive events

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-12
"""

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE TABLE archive_events (
            archive_id UUID PRIMARY KEY,
            trace_id VARCHAR(64) NOT NULL,
            archived_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            storage_uri VARCHAR(256) NOT NULL
        )
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP TABLE archive_events
        """
    )
