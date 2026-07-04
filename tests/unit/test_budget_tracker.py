#!/usr/bin/env python3
"""
test_budget_tracker.py --- unit tests for token and tool-call budget tracking

Contains:
    test_fresh_tracker_not_exhausted(): verifies a new tracker has headroom
    test_recording_tokens_accumulates(): verifies token recording accumulates
"""

from apps.api.budget.tracker import BudgetLimits, BudgetTracker


def test_fresh_tracker_not_exhausted() -> None:
    """Verifies a new tracker has headroom."""
    assert BudgetTracker().is_exhausted() is False


def test_recording_tokens_accumulates() -> None:
    """Verifies token recording accumulates."""
    tracker = BudgetTracker()
    tracker.record_tokens(100)
    tracker.record_tokens(50)
    assert tracker.tokens_used == 150


def test_tool_call_recording_accumulates() -> None:
    """Verifies tool-call recording accumulates."""
    tracker = BudgetTracker()
    tracker.record_tool_call()
    tracker.record_tool_call()
    assert tracker.tool_calls_made == 2


def test_remaining_decreases_with_use() -> None:
    """Verifies remaining headroom shrinks as budget is consumed."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=1000, max_tool_calls=10))
    tracker.record_tokens(400)
    assert tracker.remaining()["tokens"] == 600


def test_usage_ratio_zero_initially() -> None:
    """Verifies a fresh tracker reports zero usage."""
    ratios = BudgetTracker().usage_ratio()
    assert ratios["tokens"] == 0.0


def test_usage_ratio_tracks_consumption() -> None:
    """Verifies the ratio reflects actual consumption."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=1000, max_tool_calls=10))
    tracker.record_tokens(500)
    assert tracker.usage_ratio()["tokens"] == 0.5


def test_exhausted_when_tokens_at_cap() -> None:
    """Verifies hitting the token cap exhausts the budget."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=100, max_tool_calls=100))
    tracker.record_tokens(100)
    assert tracker.is_exhausted() is True


def test_exhausted_when_tool_calls_at_cap() -> None:
    """Verifies hitting the tool-call cap exhausts the budget."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=1000, max_tool_calls=2))
    tracker.record_tool_call()
    tracker.record_tool_call()
    assert tracker.is_exhausted() is True


def test_check_raises_on_token_cap() -> None:
    """Verifies check raises BudgetExhaustedError at the token cap."""
    from apps.api.budget.tracker import BudgetExhaustedError

    tracker = BudgetTracker(BudgetLimits(max_tokens=10, max_tool_calls=10))
    tracker.record_tokens(10)
    try:
        tracker.check()
    except BudgetExhaustedError as exc:
        assert exc.resource == "tokens"
        return
    raise AssertionError("expected BudgetExhaustedError")


def test_check_raises_on_tool_call_cap() -> None:
    """Verifies check raises BudgetExhaustedError at the tool-call cap."""
    from apps.api.budget.tracker import BudgetExhaustedError

    tracker = BudgetTracker(BudgetLimits(max_tokens=100, max_tool_calls=1))
    tracker.record_tool_call()
    try:
        tracker.check()
    except BudgetExhaustedError as exc:
        assert exc.resource == "tool_calls"
        return
    raise AssertionError("expected BudgetExhaustedError")


def test_check_passes_with_headroom() -> None:
    """Verifies check does not raise with budget left."""
    BudgetTracker().check()


def test_reset_clears_consumption() -> None:
    """Verifies reset returns the tracker to a fresh state."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=10, max_tool_calls=1))
    tracker.record_tokens(10)
    tracker.reset()
    assert tracker.tokens_used == 0
    assert tracker.is_exhausted() is False


def test_budget_exhausted_error_message() -> None:
    """Verifies the error message names the exhausted resource."""
    from apps.api.budget.tracker import BudgetExhaustedError

    assert "tokens" in str(BudgetExhaustedError("tokens"))


def test_snapshot_contains_usage_and_limits() -> None:
    """Verifies the snapshot carries usage and limits."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=100, max_tool_calls=5))
    tracker.record_tokens(25)
    snapshot = tracker.snapshot()
    assert snapshot["tokens_used"] == 25
    assert snapshot["max_tokens"] == 100


def test_limits_default_values() -> None:
    """Verifies the default limits match the shipped configuration."""
    limits = BudgetLimits()
    assert limits.max_tokens == 50_000
    assert limits.max_tool_calls == 40


def test_remaining_tool_calls() -> None:
    """Verifies remaining tool-call headroom is reported."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=100, max_tool_calls=4))
    tracker.record_tool_call()
    assert tracker.remaining()["tool_calls"] == 3


def test_is_near_limit_flags_high_usage() -> None:
    """Verifies the near-limit flag trips past the threshold."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=100, max_tool_calls=100))
    tracker.record_tokens(90)
    assert tracker.is_near_limit() is True


def test_is_near_limit_false_when_low() -> None:
    """Verifies low usage stays below the near-limit threshold."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=100, max_tool_calls=100))
    tracker.record_tokens(10)
    assert tracker.is_near_limit() is False


def test_usage_ratio_tool_calls_component() -> None:
    """Verifies the tool-call component of the usage ratio."""
    tracker = BudgetTracker(BudgetLimits(max_tokens=100, max_tool_calls=10))
    tracker.record_tool_call()
    assert tracker.usage_ratio()["tool_calls"] == 0.1


def test_tracker_limits_stored() -> None:
    """Verifies the tracker keeps the limits it was built with."""
    limits = BudgetLimits(max_tokens=5, max_tool_calls=5)
    assert BudgetTracker(limits).limits is limits
