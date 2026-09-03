#!/usr/bin/env python3
"""
tracker.py --- token and tool-call budget tracking per session

Contains:
    BudgetLimits: caps on tokens and tool calls per session
    BudgetTracker: records consumption and flags exhausted budgets
    BudgetTracker.check(): raises when any budget is exhausted
    BudgetTracker.usage_ratio(): consumption as fraction of limits
    BudgetTracker.snapshot(): serializes consumption for audit events
    BudgetExhaustedError: raised when a call would exceed the budget
    _ratio(): computes a consumption fraction, guarding a zero limit
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BudgetLimits:
    """Declares the budget caps for one session.

    Attributes:
        max_tokens: Maximum total tokens a session may consume.
        max_tool_calls: Maximum governed tool calls a session may make.
    """

    max_tokens: int = 50_000
    max_tool_calls: int = 40  # per-session caps; tenants can override


class BudgetTracker:
    """Records consumption and flags exhausted budgets.

    Attributes:
        limits: The budget caps enforced for the session.
        tokens_used: Tokens consumed so far.
        tool_calls_made: Tool calls made so far.
    """

    def __init__(self, limits: BudgetLimits | None = None) -> None:
        """Initializes the tracker with limits.

        Args:
            limits: The budget caps enforced for the session.
        """
        self.limits = limits if limits is not None else BudgetLimits()
        self.tokens_used = 0
        self.tool_calls_made = 0

    def record_tokens(self, count: int) -> None:
        """Records token consumption.

        Args:
            count: Tokens consumed by the latest model call.
        """
        self.tokens_used += count

    def record_tool_call(self) -> None:
        """Records one governed tool call."""
        self.tool_calls_made += 1

    def is_exhausted(self) -> bool:
        """Reports whether any budget is exhausted.

        Returns:
            exhausted: True when tokens or tool calls are at the cap.
        """
        return (
            self.tokens_used >= self.limits.max_tokens
            or self.tool_calls_made >= self.limits.max_tool_calls
        )

    def remaining(self) -> dict[str, Any]:
        """Reports remaining budget headroom.

        Returns:
            remaining: Tokens and tool calls left before exhaustion.
        """
        return {
            "tokens": self.limits.max_tokens - self.tokens_used,
            "tool_calls": self.limits.max_tool_calls - self.tool_calls_made,
        }

    def usage_ratio(self) -> dict[str, Any]:
        """Computes consumption as a fraction of each limit.

        Returns:
            ratio: tokens and tool_calls consumed as 0.0-1.0 fractions.
        """
        return {
            "tokens": _ratio(self.tokens_used, self.limits.max_tokens),
            "tool_calls": _ratio(self.tool_calls_made, self.limits.max_tool_calls),
        }

    def check(self) -> None:
        """Raises when any budget is exhausted.

        Raises:
            BudgetExhaustedError: When tokens or tool calls are at the cap.
        """
        if self.tokens_used >= self.limits.max_tokens:
            raise BudgetExhaustedError("tokens")
        if self.tool_calls_made >= self.limits.max_tool_calls:
            raise BudgetExhaustedError("tool_calls")

    def reset(self) -> None:
        """Resets all consumption counters to zero."""
        self.tokens_used = 0
        self.tool_calls_made = 0

    def snapshot(self) -> dict[str, Any]:
        """Serializes current consumption for audit events.

        Returns:
            snapshot: Consumption and limits as a JSON-ready dict.
        """
        return {
            "tokens_used": self.tokens_used,
            "tool_calls_made": self.tool_calls_made,
            "max_tokens": self.limits.max_tokens,
            "max_tool_calls": self.limits.max_tool_calls,
        }

    def is_near_limit(self, threshold: float = 0.8) -> bool:
        """Reports whether any budget is above the given usage fraction.

        Args:
            threshold: Usage fraction treated as near-limit.

        Returns:
            near_limit: True when any budget is past the threshold.
        """
        ratios = self.usage_ratio()
        return any(ratio >= threshold for ratio in ratios.values())


def _ratio(used: int, limit: int) -> float:
    """Computes a consumption fraction, treating a zero limit as exhausted.

    Args:
        used: Amount consumed so far.
        limit: Cap the consumption is measured against.

    Returns:
        ratio: Consumption as a 0.0-1.0 fraction; 1.0 when the limit is zero.
    """
    if limit <= 0:
        return 1.0
    return used / limit


class BudgetExhaustedError(Exception):
    """Raised when a call would exceed the session budget."""

    def __init__(self, resource: str) -> None:
        """Initializes the error with the exhausted resource name.

        Args:
            resource: Which budget ran out: tokens or tool_calls.
        """
        super().__init__(f"budget exhausted: {resource}")
        self.resource = resource
