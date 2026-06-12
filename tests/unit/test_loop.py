#!/usr/bin/env python3
"""
test_loop.py --- unit tests for the bounded orchestration loop

Contains:
    test_run_session_returns_iterations(): verifies the result shape of a session
"""

from apps.api.orchestration.loop import run_session


async def test_run_session_returns_iterations() -> None:
    """Verifies the result shape of a session."""
    result = await run_session("session-1", "write a haiku")
    assert "iterations" in result
    assert "output" in result


def test_session_summary_mentions_iterations() -> None:
    """Verifies the summary line carries the iteration count."""
    from apps.api.orchestration.loop import session_summary

    assert "3" in session_summary({"iterations": 3})


async def test_run_session_returns_dict() -> None:
    """Verifies the loop result is a plain dict for serialization."""
    result = await run_session("session-2", "ping")
    assert isinstance(result, dict)


async def test_run_session_marks_completed_status() -> None:
    """Verifies a session that the critic accepts ends completed."""
    result = await run_session("session-3", "summarize this")
    assert result["status"] == "completed"


async def test_run_session_status_known_values() -> None:
    """Verifies the status field is one of the known values."""
    result = await run_session("session-4", "draft an email")
    assert result["status"] in ("completed", "revision-bounded")


async def test_status_value_is_string() -> None:
    """Verifies the status field is always a string."""
    result = await run_session("session-5", "check status")
    assert isinstance(result["status"], str)


def test_loop_hooks_methods_are_async() -> None:
    """Verifies the hooks surface is fully awaitable."""
    import inspect

    from apps.api.orchestration.loop import LoopHooks

    assert inspect.iscoroutinefunction(LoopHooks.on_iteration)
    assert inspect.iscoroutinefunction(LoopHooks.on_complete)
