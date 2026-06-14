#!/usr/bin/env python3
"""
breaker.py --- per-downstream-server circuit breaker and bulkhead

Contains:
    ServerCircuitBreaker: trips calls to one failing downstream server
    Bulkhead: caps concurrent calls to one downstream server
    BreakerRegistry: keeps one circuit breaker per downstream server
    CircuitOpenError: raised when calling through an open breaker
"""

import asyncio
import time


class ServerCircuitBreaker:
    """Trips calls to one failing downstream server.

    Attributes:
        server_name: Downstream server this breaker guards.
        failure_threshold: Consecutive failures tolerated before opening.
        reset_seconds: Cooldown before allowing a probe call.
    """

    def __init__(
        self, server_name: str, failure_threshold: int = 5, reset_seconds: float = 15.0
    ) -> None:
        """Initializes the breaker for one downstream server.

        Args:
            server_name: Downstream server this breaker guards.
            failure_threshold: Consecutive failures tolerated before opening.
            reset_seconds: Cooldown before allowing a probe call.
        """
        self.server_name = server_name
        self.failure_threshold = failure_threshold
        self.reset_seconds = reset_seconds
        self._consecutive_failures = 0
        self._opened_at: float | None = None

    def record_success(self) -> None:
        """Records a successful call, closing the breaker."""
        self._consecutive_failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        """Records a failed call, opening the breaker at the threshold."""
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.failure_threshold:
            self._opened_at = time.time()

    def allows_call(self) -> bool:
        """Reports whether a call may proceed.

        Returns:
            allowed: False while the breaker is open inside its cooldown.
        """
        if self._opened_at is None:
            return True
        return time.time() - self._opened_at >= self.reset_seconds

    def check(self) -> None:
        """Raises when the breaker is open.

        Raises:
            CircuitOpenError: When the breaker is open.
        """
        if not self.allows_call():
            raise CircuitOpenError(self.server_name)


class Bulkhead:
    """Caps concurrent calls to one downstream server.

    Attributes:
        limit: Maximum concurrent in-flight calls.
    """

    def __init__(self, limit: int = 32, acquire_timeout: float = 2.0) -> None:
        """Initializes the bulkhead with a concurrency cap.

        Args:
            limit: Maximum concurrent in-flight calls.
        """
        self.limit = limit
        self.acquire_timeout = acquire_timeout
        self._semaphore = asyncio.Semaphore(limit)

    async def __aenter__(self) -> "Bulkhead":
        """Acquires a bulkhead slot.

        Returns:
            bulkhead: The bulkhead instance with an acquired slot.
        """
        await self._semaphore.acquire()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Releases the bulkhead slot.

        Args:
            exc_info: Exception details from the with block, if any.
        """
        self._semaphore.release()


class CircuitOpenError(Exception):
    """Raised when a call is attempted through an open server breaker."""

    def __init__(self, server_name: str) -> None:
        """Initializes the error with the guarded server's name.

        Args:
            server_name: Downstream server whose breaker is open.
        """
        super().__init__(f"circuit open for server: {server_name}")
        self.server_name = server_name


    def in_flight(self) -> int:
        """Reports the number of currently held bulkhead slots.

        Returns:
            count: Slots currently acquired.
        """
        acquired = self.limit - self._semaphore._value
        return max(acquired, 0)


class BreakerRegistry:
    """Keeps one circuit breaker per downstream server.

    Attributes:
        breakers: Server breakers keyed by server name.
        failure_threshold: Threshold applied to newly created breakers.
    """

    def __init__(self, failure_threshold: int = 5) -> None:
        """Initializes the registry with a shared threshold.

        Args:
            failure_threshold: Threshold applied to newly created breakers.
        """
        self.breakers: dict[str, ServerCircuitBreaker] = {}
        self.failure_threshold = failure_threshold

    def for_server(self, server_name: str) -> ServerCircuitBreaker:
        """Returns the breaker for a server, creating it on first use.

        Args:
            server_name: Downstream server name.

        Returns:
            breaker: The server's circuit breaker.
        """
        if server_name not in self.breakers:
            self.breakers[server_name] = ServerCircuitBreaker(
                server_name, failure_threshold=self.failure_threshold
            )
        return self.breakers[server_name]
