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
