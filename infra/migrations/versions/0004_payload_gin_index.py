#!/usr/bin/env python3
"""
0004_payload_gin_index.py --- payload gin index

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-15
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_events_payload ON audit_events USING gin (payload jsonb_path_ops)
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP INDEX ix_audit_events_payload
        """
    )
