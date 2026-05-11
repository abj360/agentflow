#!/usr/bin/env python3
"""
breaker.py --- circuit breaker that trips on budget breaches

Contains:
    CircuitOpenError: raised when calls are attempted through an open circuit
    BudgetCircuitBreaker: trips after repeated budget breaches
"""

import time


class CircuitOpenError(Exception):
    """Raised when calls are attempted through an open circuit."""


class BudgetCircuitBreaker:
    """Trips after repeated budget breaches.

    Attributes:
        failure_threshold: Breaches tolerated before the breaker opens.
        reset_seconds: Cooldown before the half-open probe is allowed.
    """

    def __init__(self, failure_threshold: int = 3, reset_seconds: float = 30.0) -> None:
        """Initializes the breaker with a threshold and cooldown.

        Args:
            failure_threshold: Breaches tolerated before the breaker opens.
            reset_seconds: Cooldown before the half-open probe is allowed.
        """
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._failures = 0
        self._opened_at: float | None = None

    def record_breach(self) -> None:
        """Records one budget breach, opening the circuit at the threshold."""
        self._failures += 1
        if self._failures >= self.failure_threshold:
            if self._opened_at is None:
                self._opened_at = time.time()

    def record_success(self) -> None:
        """Records one successful call, resetting the breach count."""
        self._failures = 0

    def is_open(self) -> bool:
        """Reports whether the circuit is currently open.

        Returns:
            open: True while the cooldown from the last trip is running.
        """
        if self._opened_at is None:
            return False
        return time.time() - self._opened_at < self.reset_seconds

    def check(self) -> None:
        """Raises when the circuit is open.

        Raises:
            CircuitOpenError: When the circuit is open.
        """
        if self.is_open():
            raise CircuitOpenError("budget circuit open")


    def reset(self) -> None:
        """Closes the circuit and clears the breach count."""
        self._failures = 0
        self._opened_at = None
