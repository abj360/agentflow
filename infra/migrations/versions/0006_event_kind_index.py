#!/usr/bin/env python3
"""
0006_event_kind_index.py --- event kind index

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-25
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_events_kind ON audit_events (kind)
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP INDEX ix_audit_events_kind
        """
    )
