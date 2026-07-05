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


def test_session_record_is_frozen() -> None:
    """Verifies session records cannot be mutated in place."""
    from dataclasses import FrozenInstanceError

    import pytest

    from apps.api.orchestration.session import SessionRecord

    record = SessionRecord(session_id="s1", version=0, trace_id="t")
    with pytest.raises(FrozenInstanceError):
        record.version = 9


def test_open_session_records_trace_id() -> None:
    """Verifies the audit trace id lands on the session record."""
    registry = SessionRegistry()
    record = registry.open_session("s2", "trace-9")
    assert record.trace_id == "trace-9"


def test_close_session_removes_record() -> None:
    """Verifies closing drops the session from the registry."""
    registry = SessionRegistry()
    registry.open_session("s3", "trace-1")
    registry.close_session("s3")
    assert "s3" not in registry.records


def test_bump_unknown_session_raises() -> None:
    """Verifies bumping an unregistered session raises KeyError."""
    registry = SessionRegistry()
    try:
        registry.bump_version("ghost")
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_version_conflict_error_is_exception() -> None:
    """Verifies the conflict error type exists for callers to catch."""
    from apps.api.orchestration.session import VersionConflictError

    assert issubclass(VersionConflictError, Exception)


def test_bump_returns_new_record_object() -> None:
    """Verifies a bump produces a new record rather than mutating."""
    registry = SessionRegistry()
    first = registry.open_session("s4", "trace-1")
    second = registry.bump_version("s4")
    assert first is not second


def test_list_sessions_returns_all() -> None:
    """Verifies listing returns every registered session."""
    registry = SessionRegistry()
    registry.open_session("s5", "trace-1")
    registry.open_session("s6", "trace-2")
    assert len(registry.list_sessions()) == 2


def test_close_unknown_session_raises() -> None:
    """Verifies closing an unregistered session raises KeyError."""
    registry = SessionRegistry()
    try:
        registry.close_session("ghost")
    except KeyError:
        return
    raise AssertionError("expected KeyError")


def test_expire_older_than_removes_stale() -> None:
    """Verifies expiry drops sessions older than the cutoff."""
    registry = SessionRegistry()
    registry.open_session("s7", "trace-1")
    assert registry.expire_older_than(0) == 1
    assert registry.list_sessions() == []
