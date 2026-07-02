#!/usr/bin/env python3
"""
0014_retention_function.py --- retention function

Contains:
    upgrade(): applies the migration
    downgrade(): reverts the migration

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-02
"""

from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Applies the migration."""
    op.execute(
        """
        CREATE OR REPLACE FUNCTION purge_events_before(cutoff timestamptz)
        RETURNS integer AS $$
        DECLARE
            purged integer;
        BEGIN
            DELETE FROM audit_events WHERE created_at < cutoff;
            GET DIAGNOSTICS purged = ROW_COUNT;
            RETURN purged;
        END;
        $$ LANGUAGE plpgsql
        """
    )


def downgrade() -> None:
    """Reverts the migration."""
    op.execute(
        """
        DROP FUNCTION purge_events_before(timestamptz)
        """
    )
