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


def test_breaker_recovers_after_cooldown() -> None:
    """Verifies the breaker allows calls again after the cooldown."""
    breaker = ServerCircuitBreaker("srv", failure_threshold=1, reset_seconds=0)
    breaker.record_failure()
    assert breaker.allows_call() is True


def test_check_raises_when_open() -> None:
    """Verifies check raises CircuitOpenError while open."""
    from apps.api.resilience.breaker import CircuitOpenError

    breaker = ServerCircuitBreaker("srv", failure_threshold=1)
    breaker.record_failure()
    try:
        breaker.check()
    except CircuitOpenError as exc:
        assert exc.server_name == "srv"
        return
    raise AssertionError("expected CircuitOpenError")


def test_open_error_names_server() -> None:
    """Verifies the open error message names the guarded server."""
    from apps.api.resilience.breaker import CircuitOpenError

    assert "search-mcp" in str(CircuitOpenError("search-mcp"))


async def test_bulkhead_counts_in_flight() -> None:
    """Verifies in_flight reflects held bulkhead slots."""
    from apps.api.resilience.breaker import Bulkhead

    bulkhead = Bulkhead(limit=4)
    async with bulkhead:
        assert bulkhead.in_flight() == 1
    assert bulkhead.in_flight() == 0


async def test_bulkhead_releases_slots() -> None:
    """Verifies slots free up after the with block."""
    from apps.api.resilience.breaker import Bulkhead

    bulkhead = Bulkhead(limit=1)
    async with bulkhead:
        pass
    async with bulkhead:
        assert bulkhead.in_flight() == 1


def test_registry_creates_breaker_per_server() -> None:
    """Verifies the registry creates breakers on demand."""
    from apps.api.resilience.breaker import BreakerRegistry

    registry = BreakerRegistry()
    assert registry.for_server("a") is not registry.for_server("b")
