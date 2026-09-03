#!/usr/bin/env python3
"""
locks.py --- Redis-backed distributed lock for critical sections

Contains:
    DistributedLock: async context manager guarding a critical section via Redis
    LockNotHeldError: raised when operating on a lock that is not held
    lock_key(): builds a namespaced Redis lock key from parts
"""

import asyncio
import time
import uuid
from typing import Protocol


class RedisLike(Protocol):
    """Structural interface for the async Redis calls the lock uses."""

    async def set(self, key: str, value: str, nx: bool = False, px: int = 0) -> object:
        """Sets a key with optional NX/PX flags."""

    async def get(self, key: str) -> object:
        """Returns the stored value for a key."""

    async def delete(self, key: str) -> object:
        """Deletes a key."""

    async def eval(self, script: str, numkeys: int, *args: str) -> object:
        """Runs a Lua script against the given keys."""

    async def pexpire(self, key: str, ttl_ms: int) -> object:
        """Sets a key's expiry in milliseconds."""


class DistributedLock:
    """Guards a critical section via a Redis SET NX PX lock.

    Attributes:
        redis: Async Redis client used for lock operations (structural RedisLike).
        key: Lock key in Redis.
        ttl_ms: Lock time-to-live in milliseconds.
    """

    def __init__(self, redis: RedisLike, key: str, ttl_ms: int = 10_000) -> None:
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

    async def acquire(self, timeout_seconds: float = 5.0) -> bool:
        """Attempts to acquire the lock within the timeout.

        Args:
            timeout: Seconds to keep retrying before giving up.

        Returns:
            acquired: True when the lock was acquired.
        """
        deadline = time.monotonic() + timeout_seconds
        token = uuid.uuid4().hex
        while time.monotonic() < deadline:
            claimed = await self.redis.set(self.key, token, nx=True, px=self.ttl_ms)
            if claimed:
                self._token = token
                return True
            await asyncio.sleep(0.05)
        return False

    async def release(self) -> None:
        """Releases the lock when held by this instance.

        Raises:
            LockNotHeldError: When release is called without holding.
        """
        if self._token is None:
            raise LockNotHeldError(self.key)
        lua = (
            "if redis.call('get', KEYS[1]) == ARGV[1] then "
            "return redis.call('del', KEYS[1]) else return 0 end"
        )
        await self.redis.eval(lua, 1, self.key, self._token)
        self._token = None

    async def __aenter__(self) -> "DistributedLock":
        """Acquires the lock, raising on timeout.

        Returns:
            lock: The acquired lock instance.

        Raises:
            TimeoutError: When the lock could not be acquired in time.
        """
        await self.acquire_or_raise()
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

    @property
    def is_held(self) -> bool:
        """Reports whether this instance currently holds the lock."""
        return self._token is not None

    async def acquire_or_raise(self, timeout_seconds: float = 5.0) -> None:
        """Acquires the lock or raises instead of returning False.

        Args:
            timeout: Seconds to keep retrying before giving up.

        Raises:
            TimeoutError: When the lock could not be acquired in time.
        """
        acquired = await self.acquire(timeout_seconds)
        if not acquired:
            raise TimeoutError(f"could not acquire lock {self.key}")


class LockNotHeldError(Exception):
    """Raised when operating on a lock that is not held."""


def lock_key(*parts: str) -> str:
    """Builds a namespaced Redis lock key from parts.

    Args:
        parts: Key components joined with colons.

    Returns:
        key: Namespaced lock key for Redis.
    """
    return "agentflow:lock:" + ":".join(parts)
