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


def test_policies_from_dict_defaults() -> None:
    """Verifies missing fields fall back to policy defaults."""
    from apps.api.orchestration.retry import policies_from_dict

    registry = policies_from_dict({"fs.read": {}})
    policy = registry.resolve("fs.read")
    assert policy.max_attempts == 3 and policy.backoff_seconds == 0.5


async def test_execute_with_retry_first_try_success() -> None:
    """Verifies a healthy call returns on the first attempt."""
    from apps.api.orchestration.retry import execute_with_retry

    async def healthy() -> str:
        """Succeeds immediately."""
        return "fine"

    policy = RetryPolicy(tool_name="t", backoff_seconds=0)
    assert await execute_with_retry(healthy, policy) == "fine"


def test_registry_starts_empty() -> None:
    """Verifies a fresh registry has no registered policies."""
    assert RetryPolicyRegistry().policies == {}


async def test_execute_with_retry_counts_attempts() -> None:
    """Verifies the attempt count matches the failure count plus one."""
    from apps.api.orchestration.retry import execute_with_retry

    calls = {"n": 0}

    async def twice_flaky() -> str:
        """Fails once then succeeds."""
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("t")
        return "ok"

    policy = RetryPolicy(tool_name="t", max_attempts=3, backoff_seconds=0)
    await execute_with_retry(twice_flaky, policy)
    assert calls["n"] == 2


def test_backoff_seconds_configurable() -> None:
    """Verifies the backoff base is part of the policy."""
    policy = RetryPolicy(tool_name="t", backoff_seconds=2.0)
    assert policy.backoff_seconds == 2.0


async def test_execute_with_retry_zero_backoff_is_fast() -> None:
    """Verifies zero backoff retries without sleeping."""
    from apps.api.orchestration.retry import execute_with_retry

    async def once_flaky() -> str:
        """Fails once then succeeds."""
        if not getattr(once_flaky, "failed", False):
            once_flaky.failed = True
            raise TimeoutError("t")
        return "ok"

    policy = RetryPolicy(tool_name="t", max_attempts=2, backoff_seconds=0)
    assert await execute_with_retry(once_flaky, policy) == "ok"


def test_retryable_errors_is_tuple() -> None:
    """Verifies retryable errors are declared as an immutable tuple."""
    policy = RetryPolicy(tool_name="t")
    assert isinstance(policy.retryable_errors, tuple)


def test_tenant_override_wins_over_default() -> None:
    """Verifies a tenant override beats the registered policy."""
    registry = RetryPolicyRegistry()
    registry.register(RetryPolicy(tool_name="shell.exec", max_attempts=2))
    registry.register_tenant_override("acme", RetryPolicy(tool_name="shell.exec", max_attempts=7))
    assert registry.resolve("shell.exec", tenant_id="acme").max_attempts == 7


def test_other_tenant_gets_default_policy() -> None:
    """Verifies tenants without an override get the registered policy."""
    registry = RetryPolicyRegistry()
    registry.register(RetryPolicy(tool_name="shell.exec", max_attempts=2))
    registry.register_tenant_override("acme", RetryPolicy(tool_name="shell.exec", max_attempts=7))
    assert registry.resolve("shell.exec", tenant_id="globex").max_attempts == 2


def test_register_overwrites_existing_policy() -> None:
    """Verifies re-registering a tool replaces its policy."""
    registry = RetryPolicyRegistry()
    registry.register(RetryPolicy(tool_name="t", max_attempts=1))
    registry.register(RetryPolicy(tool_name="t", max_attempts=5))
    assert registry.resolve("t").max_attempts == 5
