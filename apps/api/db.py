#!/usr/bin/env python3
"""
db.py --- async Postgres engine and session factory

Contains:
    get_engine(): builds (and caches) the async SQLAlchemy engine
    get_session_factory(): returns the async session factory bound to the engine
    get_session(): FastAPI dependency yielding an async session
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from apps.api.config import get_settings

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine():
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
            pool_recycle=1800,
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

    Yields:
        session: Async session bound to the shared engine.
    """
    async with get_session_factory()() as session:
        yield session
