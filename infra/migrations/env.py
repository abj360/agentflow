#!/usr/bin/env python3
"""
env.py --- Alembic migration environment wiring

Contains:
    run_migrations_offline(): emits SQL without a database connection
    do_run_migrations(): runs migrations on an open connection
    run_migrations_online(): runs migrations against a live connection
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from apps.api.audit.models import Base
from apps.api.config import get_settings

config = context.config

# model metadata drives --autogenerate diffs; keep imports current
target_metadata = Base.metadata

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def run_migrations_offline() -> None:
    """Emits SQL without a database connection."""
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Runs migrations on an open connection.

    Args:
        connection: Open SQLAlchemy connection provided by the runner.
    """
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Runs migrations against a live connection."""
    engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
