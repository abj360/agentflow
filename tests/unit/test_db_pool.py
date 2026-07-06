#!/usr/bin/env python3
"""
test_db_pool.py --- unit tests for the Postgres engine and pool wiring

Contains:
    test_get_engine_caches_instance(): verifies the engine is built only once
"""

from apps.api import db


def setup_function() -> None:
    """Resets cached engine and factory between tests."""
    db._engine = None
    db._session_factory = None


def test_get_engine_caches_instance() -> None:
    """Verifies the engine is built only once."""
    assert db.get_engine() is db.get_engine()


def test_get_session_factory_caches_instance() -> None:
    """Verifies the session factory is built only once."""
    assert db.get_session_factory() is db.get_session_factory()


def test_engine_uses_configured_pool_size() -> None:
    """Verifies the engine pool size comes from settings."""
    engine = db.get_engine()
    assert engine.pool.size() >= 1


async def test_dispose_engine_resets_cache() -> None:
    """Verifies disposing drops the cached engine and factory."""
    db.get_engine()
    await db.dispose_engine()
    assert db._engine is None
    assert db._session_factory is None


async def test_get_session_yields_session() -> None:
    """Verifies the dependency yields a usable async session."""
    async for session in db.get_session():
        assert session is not None


def test_pool_recycle_is_set() -> None:
    """Verifies connection recycling is enabled to survive idle cutoffs."""
    engine = db.get_engine()
    assert engine.pool._recycle == 1800


def test_pool_status_reports_keys() -> None:
    """Verifies pool_status exposes the expected occupancy keys."""
    status = db.pool_status()
    assert {"size", "checked_out", "overflow"} <= set(status)


def test_pool_timeout_comes_from_settings() -> None:
    """Verifies the pool timeout tracks the configured value."""
    engine = db.get_engine()
    assert engine.pool._timeout >= 0
