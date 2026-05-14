#!/usr/bin/env python3
"""
test_session.py --- unit tests for versioned session records

Contains:
    test_open_session_starts_at_zero(): verifies new sessions begin at version 0
    test_bump_version_increments(): verifies bumps increment the version
"""

from apps.api.orchestration.session import SessionRegistry


def test_open_session_starts_at_zero() -> None:
    """Verifies new sessions begin at version 0."""
    registry = SessionRegistry()
    record = registry.open_session("s1", "trace-1")
    assert record.version == 0


def test_bump_version_increments() -> None:
    """Verifies bumps increment the version."""
    registry = SessionRegistry()
    registry.open_session("s1", "trace-1")
    assert registry.bump_version("s1").version == 1
