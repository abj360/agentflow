#!/usr/bin/env python3
"""
test_rate_limit.py --- unit tests for the fixed-window rate limiting middleware

Contains:
    test_allows_requests_under_limit(): verifies requests below the cap pass through
    test_rejects_request_over_limit(): verifies the (n+1)th request gets a 429
"""

from types import SimpleNamespace

from starlette.responses import Response

from apps.api.middleware.rate_limit import RateLimitMiddleware, RedisRateCounter


class FakeRequest:
    """Mimics the request attributes the middleware reads."""

    def __init__(self, host: str = "127.0.0.1") -> None:
        """Stores the fake client host."""
        self.client = SimpleNamespace(host=host)


async def passthrough(_request: object) -> Response:
    """Returns a sentinel response for allowed requests."""
    return Response("ok")


def build_middleware(max_requests: int = 2) -> RateLimitMiddleware:
    """Builds a middleware instance around a dummy ASGI app.

    Args:
        max_requests: Maximum requests allowed per client per window.

    Returns:
        middleware: Configured rate limiting middleware for tests.
    """

    async def app(_scope: dict, _receive: object, _send: object) -> None:
        """Dummy ASGI app."""

    return RateLimitMiddleware(app, max_requests=max_requests, window_seconds=60)


async def test_allows_requests_under_limit() -> None:
    """Verifies requests below the cap pass through."""
    middleware = build_middleware(max_requests=2)
    response = await middleware.dispatch(FakeRequest(), passthrough)
    assert response.status_code == 200


async def test_rejects_request_over_limit() -> None:
    """Verifies the (n+1)th request gets a 429."""
    middleware = build_middleware(max_requests=1)
    await middleware.dispatch(FakeRequest(), passthrough)
    response = await middleware.dispatch(FakeRequest(), passthrough)
    assert response.status_code == 429


async def test_separate_clients_have_separate_counters() -> None:
    """Verifies one client's burst does not consume another's allowance."""
    middleware = build_middleware(max_requests=1)
    await middleware.dispatch(FakeRequest("10.0.0.1"), passthrough)
    response = await middleware.dispatch(FakeRequest("10.0.0.2"), passthrough)
    assert response.status_code == 200


async def test_429_body_says_rate_limited() -> None:
    """Verifies the rejection body explains why the request failed."""
    middleware = build_middleware(max_requests=1)
    await middleware.dispatch(FakeRequest(), passthrough)
    response = await middleware.dispatch(FakeRequest(), passthrough)
    assert b"rate limit exceeded" in response.body


async def test_429_body_includes_retry_after() -> None:
    """Verifies the rejection body tells clients when to retry."""
    middleware = build_middleware(max_requests=1)
    await middleware.dispatch(FakeRequest(), passthrough)
    response = await middleware.dispatch(FakeRequest(), passthrough)
    assert b"retry_after" in response.body


class FakeRedis:
    """Mimics the async Redis calls the counter uses."""

    def __init__(self) -> None:
        """Initializes empty counters and expiry records."""
        self.counts: dict = {}
        self.expiries: dict = {}

    async def incr(self, key: str) -> int:
        """Increments the stored count for a key."""
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> None:
        """Records the expiry set for a key."""
        self.expiries[key] = seconds
