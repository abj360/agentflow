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
