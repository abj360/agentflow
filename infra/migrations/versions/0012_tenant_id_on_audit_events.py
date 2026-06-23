#!/usr/bin/env python3
"""
0012_tenant_id_on_audit_events.py --- tenant id on audit events

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-23
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        ALTER TABLE audit_events ADD COLUMN tenant_id VARCHAR(64) NOT NULL DEFAULT 'default'
        """
    )
    op.execute(
        """
        UPDATE audit_events SET tenant_id = 'legacy' WHERE trace_id LIKE 'import-%'
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        ALTER TABLE audit_events DROP COLUMN tenant_id
        """
    )
