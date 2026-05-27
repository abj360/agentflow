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
