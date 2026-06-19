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


async def test_extend_fails_when_not_held() -> None:
    """Verifies extending a lock we don't hold reports False."""
    lock = DistributedLock(FakeRedis(), "k1")
    assert await lock.extend() is False


async def test_release_clears_key() -> None:
    """Verifies releasing removes the lock key."""
    redis = FakeRedis()
    lock = DistributedLock(redis, "k1")
    await lock.acquire()
    await lock.release()
    assert redis.store == {}


async def test_release_without_holding_raises() -> None:
    """Verifies releasing an unheld lock raises LockNotHeldError."""
    from apps.api.concurrency.locks import LockNotHeldError

    lock = DistributedLock(FakeRedis(), "k1")
    try:
        await lock.release()
    except LockNotHeldError:
        return
    raise AssertionError("expected LockNotHeldError")


async def test_release_keeps_others_key() -> None:
    """Verifies releasing does not delete someone else's lock key."""
    redis = FakeRedis()
    redis.store["k1"] = "other-token"
    lock = DistributedLock(redis, "k1")
    lock._token = "our-token"
    await lock.release()
    assert redis.store.get("k1") == "other-token"


async def test_context_manager_acquires_and_releases() -> None:
    """Verifies the async context manager acquires and releases."""
    redis = FakeRedis()
    async with DistributedLock(redis, "k1"):
        assert redis.store.get("k1") is not None
    assert redis.store == {}


async def test_context_manager_raises_on_timeout() -> None:
    """Verifies the context manager raises when the lock is held."""
    redis = FakeRedis()
    holder = DistributedLock(redis, "k1")
    await holder.acquire()
    try:
        async with DistributedLock(redis, "k1", ttl_ms=1000):
            pass
    except TimeoutError:
        return
    raise AssertionError("expected TimeoutError")


async def test_release_uses_atomic_eval() -> None:
    """Verifies release goes through the compare-and-delete script."""
    redis = FakeRedis()
    calls = []

    async def eval(self, script: str, keys: int, key: str, token: str) -> int:
        """Records the eval invocation and applies it."""
        calls.append(key)
        if self.store.get(key) == token:
            self.store.pop(key, None)
        return 1

    redis.eval = eval.__get__(redis)
    lock = DistributedLock(redis, "k1")
    await lock.acquire()
    await lock.release()
    assert calls == ["k1"]


async def test_is_held_tracks_state() -> None:
    """Verifies is_held reflects acquisition and release."""
    lock = DistributedLock(FakeRedis(), "k1")
    assert lock.is_held is False
    await lock.acquire()
    assert lock.is_held is True


async def test_is_held_false_after_release() -> None:
    """Verifies is_held clears after release."""
    lock = DistributedLock(FakeRedis(), "k1")
    await lock.acquire()
    await lock.release()
    assert lock.is_held is False


async def test_acquire_or_raise_succeeds() -> None:
    """Verifies acquire_or_raise acquires a free lock."""
    lock = DistributedLock(FakeRedis(), "k1")
    await lock.acquire_or_raise()
    assert lock.is_held is True


async def test_acquire_or_raise_times_out() -> None:
    """Verifies acquire_or_raise raises when the lock stays held."""
    redis = FakeRedis()
    holder = DistributedLock(redis, "k1")
    await holder.acquire()
    try:
        await DistributedLock(redis, "k1").acquire_or_raise(timeout=0.2)
    except TimeoutError:
        return
    raise AssertionError("expected TimeoutError")


def test_lock_key_builds_namespaced_key() -> None:
    """Verifies lock keys are namespaced with colons."""
    from apps.api.concurrency.locks import lock_key

    assert lock_key("audit", "trace-1") == "agentflow:lock:audit:trace-1"
