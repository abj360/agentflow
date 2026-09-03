#!/usr/bin/env python3
"""
test_retry_backoff.py --- unit tests for downstream call retries

Contains:
    test_succeeds_after_transient_failure(): verifies retries recover a call
"""

from apps.api.resilience.retry import call_with_retries


async def test_succeeds_after_transient_failure() -> None:
    """Verifies retries recover a call."""
    calls = {"n": 0}

    async def flaky() -> str:
        """Fails once then succeeds."""
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectionError("mcp server unreachable")
        return "ok"

    assert await call_with_retries(flaky) == "ok"


async def test_gives_up_after_max_retries() -> None:
    """Verifies a persistently failing call raises."""

    async def always_down() -> str:
        """Always fails."""
        raise ConnectionError("down")

    try:
        await call_with_retries(always_down, max_retries=1)
    except ConnectionError:
        return
    raise AssertionError("expected ConnectionError")


async def test_first_try_success_returns_immediately() -> None:
    """Verifies a healthy call needs no retries."""
    calls = {"n": 0}

    async def healthy() -> str:
        """Succeeds immediately."""
        calls["n"] += 1
        return "ok"

    assert await call_with_retries(healthy) == "ok"
    assert calls["n"] == 1
