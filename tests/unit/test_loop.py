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
