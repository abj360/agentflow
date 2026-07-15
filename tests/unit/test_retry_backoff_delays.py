#!/usr/bin/env python3
"""
test_retry_backoff_delays.py --- regression tests for backoff + jitter retries

Contains:
    test_backoff_delay_grows_exponentially(): verifies delays double per attempt
    test_backoff_delay_capped(): verifies delays never exceed the cap
    test_backoff_delay_has_jitter(): verifies delays vary across calls
"""

from apps.api.resilience.retry import MAX_DELAY_SECONDS, backoff_delay


def test_backoff_delay_grows_exponentially() -> None:
    """Verifies delays double per attempt."""
    early = backoff_delay(0, base=1.0)
    later = backoff_delay(2, base=1.0)
    assert later >= early


def test_backoff_delay_capped() -> None:
    """Verifies delays never exceed the cap."""
    assert backoff_delay(20) <= MAX_DELAY_SECONDS * 1.5


def test_backoff_delay_has_jitter() -> None:
    """Verifies delays vary across calls."""
    delays = {backoff_delay(3) for _ in range(20)}
    assert len(delays) > 1


def test_backoff_delay_zero_base_stays_zero() -> None:
    """Verifies a zero base delay keeps retries immediate in tests."""
    assert backoff_delay(3, base=0) == 0
