#!/usr/bin/env python3
"""
0013_tenant_index.py --- tenant index

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-25
"""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_audit_events_tenant ON audit_events (tenant_id)
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP INDEX ix_audit_events_tenant
        """
    )
