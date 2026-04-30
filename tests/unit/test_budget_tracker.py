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
