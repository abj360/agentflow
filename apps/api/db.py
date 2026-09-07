#!/usr/bin/env python3
"""
db.py --- async Postgres engine and session factory

Contains:
    DatastoreUnavailable: raised when the audit database cannot be reached
    get_engine(): builds (and caches) the async SQLAlchemy engine
    get_session_factory(): returns the async session factory bound to the engine
    get_session(): FastAPI dependency yielding an async session
    dispose_engine(): disposes the shared engine and resets cached factories
    pool_status(): reports current connection pool occupancy
"""

from collections.abc import AsyncIterator
from typing import Any, cast

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import QueuePool

from apps.api.config import get_settings


class DatastoreUnavailable(RuntimeError):
    """Raised when the audit database cannot be reached for a request."""


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Builds (and caches) the async SQLAlchemy engine.

    Returns:
        engine: Shared async engine bound to the configured database URL.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_pre_ping=True,
            pool_recycle=1800,  # recycle connections before the LB idle cutoff
            pool_timeout=settings.db_pool_timeout,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Returns the async session factory bound to the engine.

    Returns:
        session_factory: Shared factory producing async sessions.
    """
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yields an async session for one request scope.

    A driver that cannot open a socket raises OSError rather than anything
    SQLAlchemy owns, so both are narrowed here into one error the API layer can
    answer with a status code instead of letting it escape as an unhandled 500.

    Yields:
        session: Async session bound to the shared engine.

    Raises:
        DatastoreUnavailable: When the database cannot be reached.
    """
    try:
        async with get_session_factory()() as session:
            yield session
    except (SQLAlchemyError, OSError) as error:
        raise DatastoreUnavailable(str(error)) from error


async def dispose_engine() -> None:
    """Disposes the shared engine and resets cached factories."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def pool_status() -> dict[str, Any]:
    """Reports current connection pool occupancy.

    Returns:
        status: Mapping of pool size, checked-out and overflow counts.
    """
    pool = cast(QueuePool, get_engine().pool)  # sync_pool exposes the raw counters
    return {
        "size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
