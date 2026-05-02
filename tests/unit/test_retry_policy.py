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
