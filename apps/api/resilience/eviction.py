#!/usr/bin/env python3
"""
eviction.py --- health-check-based eviction of unhealthy MCP servers

Contains:
    HealthChecker: probes servers and tracks consecutive failures
    ServerEvictor: evicts servers failing health checks
    ServerEvictor.evict(): evicts a server immediately
    ServerEvictor.reinstate(): reinstates an evicted server
    ServerEvictor.eviction_age(): how long a server has been evicted
"""

import time


class HealthChecker:
    """Probes servers and tracks consecutive failures.

    Attributes:
        failure_threshold: Consecutive failed probes before a server is unhealthy.
        failures: Consecutive failure counts keyed by server name.
    """

    def __init__(self, failure_threshold: int = 3) -> None:
        """Initializes the checker with a failure threshold.

        Args:
            failure_threshold: Consecutive failed probes before unhealthy.
        """
        self.failure_threshold = failure_threshold
        self.failures: dict[str, int] = {}

    def record_probe(self, server_name: str, ok: bool) -> bool:
        """Records one probe outcome.

        Args:
            server_name: The probed server.
            ok: Whether the probe succeeded.

        Returns:
            healthy: True when the server is still considered healthy.
        """
        if ok:
            self.failures[server_name] = 0
            return True
        self.failures[server_name] = self.failures.get(server_name, 0) + 1
        return self.failures[server_name] < self.failure_threshold


class ServerEvictor:
    """Evicts servers failing health checks.

    Attributes:
        checker: Health checker tracking probe outcomes.
        evicted: Currently evicted servers with eviction timestamps.
    """

    def __init__(self, checker: HealthChecker) -> None:
        """Initializes the evictor with a health checker.

        Args:
            checker: Health checker tracking probe outcomes.
        """
        self.checker = checker
        self.evicted: dict[str, float] = {}

    def probe(self, server_name: str, ok: bool) -> bool:
        """Probes a server, evicting it when it stays unhealthy.

        Args:
            server_name: The probed server.
            ok: Whether the probe succeeded.

        Returns:
            active: True when the server remains in the active pool.
        """
        healthy = self.checker.record_probe(server_name, ok)
        if not healthy:
            self.evicted[server_name] = time.time()
        return healthy

    def is_active(self, server_name: str) -> bool:
        """Reports whether a server is in the active pool.

        Args:
            server_name: The server to check.

        Returns:
            active: True when the server has not been evicted.
        """
        return server_name not in self.evicted

    def evict(self, server_name: str) -> None:
        """Evicts a server immediately, bypassing the probe path.

        Args:
            server_name: The server to evict.
        """
        self.evicted[server_name] = time.time()

    def reinstate(self, server_name: str) -> bool:
        """Reinstates an evicted server after a successful manual probe.

        Args:
            server_name: The server to reinstate.

        Returns:
            reinstated: True when the server was evicted and is now active.
        """
        if server_name not in self.evicted:
            return False
        del self.evicted[server_name]
        self.checker.failures[server_name] = 0
        return True


    def list_evicted(self) -> list[str]:
        """Lists currently evicted servers.

        Returns:
            servers: Names of all evicted servers.
        """
        return list(self.evicted)


    def eviction_age(self, server_name: str) -> float | None:
        """Reports how long a server has been evicted.

        Args:
            server_name: The evicted server.

        Returns:
            age: Seconds since eviction, or None when not evicted.
        """
        evicted_at = self.evicted.get(server_name)
        if evicted_at is None:
            return None
        return time.time() - evicted_at
