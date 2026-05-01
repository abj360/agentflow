#!/usr/bin/env python3
"""
test_resilience_breaker.py --- unit tests for the per-server circuit breaker

Contains:
    test_breaker_starts_closed(): verifies a new breaker allows calls
    test_breaker_opens_after_threshold(): verifies failures trip the breaker
"""

from apps.api.resilience.breaker import ServerCircuitBreaker


def test_breaker_starts_closed() -> None:
    """Verifies a new breaker allows calls."""
    breaker = ServerCircuitBreaker("search-mcp")
    assert breaker.allows_call() is True


def test_breaker_opens_after_threshold() -> None:
    """Verifies failures trip the breaker."""
    breaker = ServerCircuitBreaker("search-mcp", failure_threshold=2)
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.allows_call() is False


def test_success_closes_breaker() -> None:
    """Verifies a success after failures closes the breaker."""
    breaker = ServerCircuitBreaker("srv", failure_threshold=2)
    breaker.record_failure()
    breaker.record_failure()
    breaker.record_success()
    assert breaker.allows_call() is True
