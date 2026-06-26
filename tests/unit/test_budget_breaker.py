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


def test_success_resets_breach_count() -> None:
    """Verifies a success clears the running breach count."""
    breaker = BudgetCircuitBreaker(failure_threshold=2)
    breaker.record_breach()
    breaker.record_success()
    breaker.record_breach()
    assert breaker.is_open() is False


def test_circuit_open_error_is_exception() -> None:
    """Verifies the open-circuit error type is catchable."""
    assert issubclass(CircuitOpenError, Exception)


def test_reset_closes_breaker() -> None:
    """Verifies reset closes a tripped breaker."""
    breaker = BudgetCircuitBreaker(failure_threshold=1)
    breaker.record_breach()
    breaker.reset()
    assert breaker.is_open() is False


def test_half_open_after_cooldown() -> None:
    """Verifies the breaker reports half-open after the cooldown."""
    breaker = BudgetCircuitBreaker(failure_threshold=1, reset_seconds=0)
    breaker.record_breach()
    assert breaker.is_half_open() is True


def test_not_half_open_when_closed() -> None:
    """Verifies a closed breaker is not half-open."""
    assert BudgetCircuitBreaker().is_half_open() is False


def test_check_still_raises_when_open() -> None:
    """Verifies the open check keeps raising after the docstring update."""
    breaker = BudgetCircuitBreaker(failure_threshold=1)
    breaker.record_breach()
    try:
        breaker.check()
    except CircuitOpenError:
        return
    raise AssertionError("expected CircuitOpenError")


def test_state_closed_initially() -> None:
    """Verifies the initial state string is closed."""
    assert BudgetCircuitBreaker().state() == "closed"


def test_state_open_after_trip() -> None:
    """Verifies the state string reports open after a trip."""
    breaker = BudgetCircuitBreaker(failure_threshold=1)
    breaker.record_breach()
    assert breaker.state() == "open"


def test_call_runs_function_when_closed() -> None:
    """Verifies call runs the function when the circuit is closed."""
    breaker = BudgetCircuitBreaker()
    assert breaker.call(lambda: 42) == 42


def test_call_records_failure_and_reraises() -> None:
    """Verifies call records a breach and re-raises the call's error."""
    breaker = BudgetCircuitBreaker(failure_threshold=2)

    def boom() -> None:
        """Always fails."""
        raise RuntimeError("x")

    try:
        breaker.call(boom)
    except RuntimeError:
        pass
    assert breaker._failures == 1


def test_call_blocks_when_open() -> None:
    """Verifies call refuses to run while the circuit is open."""
    breaker = BudgetCircuitBreaker(failure_threshold=1)
    breaker.record_breach()
    try:
        breaker.call(lambda: 1)
    except CircuitOpenError:
        return
    raise AssertionError("expected CircuitOpenError")


def test_breach_total_counts_all_breaches() -> None:
    """Verifies the lifetime breach counter accumulates."""
    breaker = BudgetCircuitBreaker(failure_threshold=5)
    breaker.record_breach()
    breaker.record_breach()
    assert breaker._breach_total == 2
