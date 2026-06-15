#!/usr/bin/env python3
"""
retry.py --- per-tool retry policy configuration

Contains:
    RetryPolicy: declares retry behavior for one tool
    RetryPolicyRegistry: resolves the retry policy for a tool call
    execute_with_retry(): runs a tool call under its retry policy
    policies_from_dict(): builds a registry from a plain dict
"""

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    """Declares retry behavior for one tool.

    Attributes:
        tool_name: Tool this policy applies to.
        max_attempts: Maximum call attempts before failing the step.
        backoff_seconds: Base delay between attempts.
        retryable_errors: Error categories worth retrying.
    """

    tool_name: str
    max_attempts: int = 3
    backoff_seconds: float = 0.5
    retryable_errors: tuple[str, ...] = ("timeout", "rate_limited")


class RetryPolicyRegistry:
    """Resolves the retry policy for a tool call.

    Attributes:
        policies: Registered policies keyed by tool name.
        default_policy: Fallback policy for unlisted tools.
    """

    def __init__(self, default_policy: RetryPolicy | None = None) -> None:
        """Initializes the registry with an optional default policy.

        Args:
            default_policy: Fallback policy for unlisted tools.
        """
        self.policies: dict[str, RetryPolicy] = {}
        self.default_policy = default_policy or RetryPolicy(tool_name="__default__")

    def register(self, policy: RetryPolicy) -> None:
        """Registers a policy for one tool.

        Args:
            policy: The retry policy to register.
        """
        self.policies[policy.tool_name] = policy

    def resolve(self, tool_name: str) -> RetryPolicy:
        """Resolves the retry policy for a tool call.

        Args:
            tool_name: Name of the tool being called.

        Returns:
            policy: The tool's policy, or the default when unlisted.
        """
        return self.policies.get(tool_name, self.default_policy)


async def execute_with_retry(func, policy: RetryPolicy):
    """Runs a tool call under its retry policy.

    Args:
        func: Awaitable callable performing the tool call.
        policy: Retry policy governing attempts and backoff.

    Returns:
        result: The tool call's return value on success.

    Raises:
        Exception: Re-raises the call's error after the final attempt.
    """
    attempt = 0
    while True:
        try:
            return await func()
        except Exception:
            attempt += 1
            if attempt >= policy.max_attempts:
                raise
            await asyncio.sleep(policy.backoff_seconds * attempt)


def policies_from_dict(raw: dict) -> RetryPolicyRegistry:
    """Builds a registry from a plain dict, e.g. parsed YAML.

    Args:
        raw: Mapping of tool names to policy fields.

    Returns:
        registry: Populated retry policy registry.
    """
    registry = RetryPolicyRegistry()
    for tool_name, fields in raw.items():
        registry.register(
            RetryPolicy(
                tool_name=tool_name,
                max_attempts=fields.get("max_attempts", 3),
                backoff_seconds=fields.get("backoff_seconds", 0.5),
            )
        )
    return registry
