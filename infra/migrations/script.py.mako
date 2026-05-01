"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    """Applies the migration."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Reverts the migration."""
    ${downgrades if downgrades else "pass"}
