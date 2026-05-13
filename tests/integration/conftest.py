#!/usr/bin/env python3
"""
conftest.py --- shared fixtures for integration tests

Contains:
    session_factory(): provides a session factory against the test database
"""

import os

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

TEST_DATABASE_URL = os.environ.get("AGENTFLOW_TEST_DATABASE_URL")

requires_database = pytest.mark.skipif(
    TEST_DATABASE_URL is None, reason="AGENTFLOW_TEST_DATABASE_URL not set"
)


@pytest.fixture
def session_factory() -> async_sessionmaker:
    """Provides a session factory against the test database.

    Returns:
        session_factory: Factory bound to the test database engine.
    """
    engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    return async_sessionmaker(engine, expire_on_commit=False)
