#!/usr/bin/env python3
"""
test_locks.py --- unit tests for the Redis-backed distributed lock

Contains:
    test_acquire_succeeds_when_free(): verifies a free lock is acquired
    test_acquire_fails_when_held(): verifies a held lock blocks acquisition
"""

from apps.api.concurrency.locks import DistributedLock


class FakeRedis:
    """Mimics the async Redis calls the lock uses."""

    def __init__(self) -> None:
        """Initializes an empty key-value store."""
        self.store: dict[str, str] = {}

    async def set(self, key: str, value: str, nx: bool = False, px: int = 0) -> bool:
        """Sets a key, honoring nx semantics."""
        if nx and key in self.store:
            return False
        self.store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        """Returns the stored value, or None."""
        return self.store.get(key)

    async def delete(self, key: str) -> None:
        """Deletes a key."""
        self.store.pop(key, None)


async def test_acquire_succeeds_when_free() -> None:
    """Verifies a free lock is acquired."""
    lock = DistributedLock(FakeRedis(), "k1")
    assert await lock.acquire() is True


async def test_acquire_fails_when_held() -> None:
    """Verifies a held lock blocks acquisition."""
    redis = FakeRedis()
    first = DistributedLock(redis, "k1")
    await first.acquire()
    second = DistributedLock(redis, "k1")
    assert await second.acquire(timeout=0.2) is False


async def test_extend_succeeds_when_held() -> None:
    """Verifies a held lock can be extended."""
    redis = FakeRedis()

    async def pexpire(self, key: str, ttl: int) -> None:
        """Records a TTL extension."""
        self.extended = (key, ttl)

    redis.pexpire = pexpire.__get__(redis)
    lock = DistributedLock(redis, "k1")
    await lock.acquire()
    assert await lock.extend() is True
