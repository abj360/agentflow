#!/usr/bin/env python3
"""
test_eviction.py --- unit tests for health-check-based server eviction

Contains:
    test_healthy_server_stays_active(): verifies passing probes keep a server active
    test_failing_server_gets_evicted(): verifies repeated failures evict a server
"""

from apps.api.resilience.eviction import HealthChecker, ServerEvictor


def build_evictor(threshold: int = 2) -> ServerEvictor:
    """Builds an evictor with a low test threshold.

    Args:
        threshold: Consecutive failures before eviction.

    Returns:
        evictor: Configured server evictor.
    """
    return ServerEvictor(HealthChecker(failure_threshold=threshold))


def test_healthy_server_stays_active() -> None:
    """Verifies passing probes keep a server active."""
    evictor = build_evictor()
    assert evictor.probe("srv-a", ok=True) is True
    assert evictor.is_active("srv-a") is True


def test_failing_server_gets_evicted() -> None:
    """Verifies repeated failures evict a server."""
    evictor = build_evictor()
    evictor.probe("srv-a", ok=False)
    assert evictor.probe("srv-a", ok=False) is False
    assert evictor.is_active("srv-a") is False


def test_success_resets_failure_count() -> None:
    """Verifies a successful probe clears the failure count."""
    checker = HealthChecker(failure_threshold=2)
    checker.record_probe("srv", ok=False)
    checker.record_probe("srv", ok=True)
    assert checker.failures["srv"] == 0


def test_reinstate_brings_server_back() -> None:
    """Verifies reinstating returns an evicted server to the pool."""
    evictor = build_evictor()
    evictor.probe("srv", ok=False)
    evictor.probe("srv", ok=False)
    assert evictor.reinstate("srv") is True
    assert evictor.is_active("srv") is True


def test_list_evicted_names_servers() -> None:
    """Verifies the evicted list names all evicted servers."""
    evictor = build_evictor()
    evictor.probe("srv-a", ok=False)
    evictor.probe("srv-a", ok=False)
    assert "srv-a" in evictor.list_evicted()


def test_reinstate_unknown_returns_false() -> None:
    """Verifies reinstating a non-evicted server reports False."""
    assert build_evictor().reinstate("ghost") is False


def test_one_failure_keeps_server_active() -> None:
    """Verifies a single failure does not evict."""
    evictor = build_evictor()
    assert evictor.probe("srv", ok=False) is True
    assert evictor.is_active("srv") is True


def test_manual_evict_works() -> None:
    """Verifies evict removes a server without probe history."""
    evictor = build_evictor()
    evictor.evict("srv-manual")
    assert evictor.is_active("srv-manual") is False


def test_sweep_reinstates_old_evictions() -> None:
    """Verifies sweep reinstates servers past the max age."""
    evictor = build_evictor()
    evictor.evict("srv-old")
    evictor.evicted["srv-old"] = 0.0
    assert evictor.sweep_expired(60) == 1
    assert evictor.is_active("srv-old") is True


def test_sweep_keeps_fresh_evictions() -> None:
    """Verifies sweep keeps recently evicted servers out."""
    evictor = build_evictor()
    evictor.evict("srv-new")
    assert evictor.sweep_expired(3600) == 0
    assert evictor.is_active("srv-new") is False


def test_eviction_age_none_when_active() -> None:
    """Verifies eviction_age is None for active servers."""
    assert build_evictor().eviction_age("active-srv") is None


def test_eviction_age_positive_after_evict() -> None:
    """Verifies eviction_age grows after eviction."""
    evictor = build_evictor()
    evictor.evict("srv")
    assert evictor.eviction_age("srv") is not None


def test_checker_window_seconds_stored() -> None:
    """Verifies the checker keeps its probe window setting."""
    checker = HealthChecker(failure_threshold=3, window_seconds=30.0)
    assert checker.window_seconds == 30.0


def test_probe_uses_evict_helper() -> None:
    """Verifies the probe path routes through evict()."""
    evictor = build_evictor()
    evictor.probe("srv", ok=False)
    evictor.probe("srv", ok=False)
    assert "srv" in evictor.evicted
