#!/usr/bin/env python3
"""
locks.py --- Redis-backed distributed lock for critical sections

Contains:
    DistributedLock: async context manager guarding a critical section via Redis
    LockNotHeldError: raised when operating on a lock that is not held
"""

import asyncio
import time
import uuid


class DistributedLock:
    """Guards a critical section via a Redis SET NX PX lock.

    Attributes:
        redis: Async Redis client used for lock operations.
        key: Lock key in Redis.
        ttl_ms: Lock time-to-live in milliseconds.
    """

    def __init__(self, redis, key: str, ttl_ms: int = 10_000) -> None:
        """Initializes the lock with a Redis client, key and TTL.

        Args:
            redis: Async Redis client used for lock operations.
            key: Lock key in Redis.
            ttl_ms: Lock time-to-live in milliseconds.
        """
        self.redis = redis
        self.key = key
        self.ttl_ms = ttl_ms
        self._token: str | None = None

    async def acquire(self, timeout: float = 5.0) -> bool:
        """Attempts to acquire the lock within the timeout.

        Args:
            timeout: Seconds to keep retrying before giving up.

        Returns:
            acquired: True when the lock was acquired.
        """
        deadline = time.monotonic() + timeout
        token = uuid.uuid4().hex
        while time.monotonic() < deadline:
            if await self.redis.set(self.key, token, nx=True, px=self.ttl_ms):
                self._token = token
                return True
            await asyncio.sleep(0.05)
        return False

    async def release(self) -> None:
        """Releases the lock when held by this instance."""
        if self._token is None:
            return
        current = await self.redis.get(self.key)
        if current == self._token:
            await self.redis.delete(self.key)
        self._token = None

    async def __aenter__(self) -> "DistributedLock":
        """Acquires the lock, raising on timeout.

        Returns:
            lock: The acquired lock instance.

        Raises:
            TimeoutError: When the lock could not be acquired in time.
        """
        acquired = await self.acquire()
        if not acquired:
            raise TimeoutError(f"could not acquire lock {self.key}")
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Releases the lock.

        Args:
            exc_info: Exception details from the with block, if any.
        """
        await self.release()


    async def extend(self, ttl_ms: int | None = None) -> bool:
        """Extends the lock TTL while still held.

        Args:
            ttl_ms: New time-to-live; defaults to the original TTL.

        Returns:
            extended: True when the lock was still held and extended.
        """
        if self._token is None:
            return False
        ttl = ttl_ms if ttl_ms is not None else self.ttl_ms
        current = await self.redis.get(self.key)
        if current != self._token:
            return False
        await self.redis.pexpire(self.key, ttl)
        return True


class LockNotHeldError(Exception):
    """Raised when operating on a lock that is not held."""
