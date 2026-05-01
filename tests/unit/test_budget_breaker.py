#!/usr/bin/env python3
"""
test_budget_breaker.py --- unit tests for the budget circuit breaker

Contains:
    test_fresh_breaker_is_closed(): verifies a new breaker allows calls
    test_breaker_opens_after_threshold(): verifies breaches trip the breaker
"""

from apps.api.budget.breaker import BudgetCircuitBreaker, CircuitOpenError


def test_fresh_breaker_is_closed() -> None:
    """Verifies a new breaker allows calls."""
    assert BudgetCircuitBreaker().is_open() is False


def test_breaker_opens_after_threshold() -> None:
    """Verifies breaches trip the breaker."""
    breaker = BudgetCircuitBreaker(failure_threshold=2)
    breaker.record_breach()
    breaker.record_breach()
    assert breaker.is_open() is True


def test_check_raises_when_open() -> None:
    """Verifies check raises CircuitOpenError while tripped."""
    breaker = BudgetCircuitBreaker(failure_threshold=1)
    breaker.record_breach()
    try:
        breaker.check()
    except CircuitOpenError:
        return
    raise AssertionError("expected CircuitOpenError")
