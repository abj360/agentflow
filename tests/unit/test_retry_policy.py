#!/usr/bin/env python3
"""
test_retry_policy.py --- unit tests for per-tool retry policy configuration

Contains:
    test_resolve_returns_registered_policy(): verifies registered tools get their policy
    test_resolve_falls_back_to_default(): verifies unlisted tools get the default
"""

from apps.api.orchestration.retry import RetryPolicy, RetryPolicyRegistry


def test_resolve_returns_registered_policy() -> None:
    """Verifies registered tools get their policy."""
    registry = RetryPolicyRegistry()
    registry.register(RetryPolicy(tool_name="shell.exec", max_attempts=1))
    assert registry.resolve("shell.exec").max_attempts == 1


def test_resolve_falls_back_to_default() -> None:
    """Verifies unlisted tools get the default."""
    registry = RetryPolicyRegistry()
    assert registry.resolve("unknown.tool").max_attempts == 3


def test_policy_is_frozen() -> None:
    """Verifies retry policies are immutable after creation."""
    from dataclasses import FrozenInstanceError

    import pytest

    policy = RetryPolicy(tool_name="t")
    with pytest.raises(FrozenInstanceError):
        policy.max_attempts = 9


def test_default_retryable_errors() -> None:
    """Verifies the default retryable error categories."""
    policy = RetryPolicy(tool_name="t")
    assert "timeout" in policy.retryable_errors


async def test_execute_with_retry_eventually_succeeds() -> None:
    """Verifies a flaky call succeeds within the attempt budget."""
    from apps.api.orchestration.retry import execute_with_retry

    calls = {"n": 0}

    async def flaky() -> str:
        """Fails twice then succeeds."""
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("slow")
        return "ok"

    policy = RetryPolicy(tool_name="t", max_attempts=4, backoff_seconds=0)
    assert await execute_with_retry(flaky, policy) == "ok"


async def test_execute_with_retry_gives_up() -> None:
    """Verifies a persistently failing call raises after the last attempt."""
    from apps.api.orchestration.retry import execute_with_retry

    async def always_fails() -> str:
        """Always raises."""
        raise RuntimeError("down")

    policy = RetryPolicy(tool_name="t", max_attempts=2, backoff_seconds=0)
    try:
        await execute_with_retry(always_fails, policy)
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError")


def test_policies_from_dict_builds_registry() -> None:
    """Verifies dict-driven registration populates policies."""
    from apps.api.orchestration.retry import policies_from_dict

    registry = policies_from_dict({"search.query": {"max_attempts": 5}})
    assert registry.resolve("search.query").max_attempts == 5
