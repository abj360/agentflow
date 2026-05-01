#!/usr/bin/env python3
"""
test_rate_limit.py --- unit tests for the fixed-window rate limiting middleware

Contains:
    test_allows_requests_under_limit(): verifies requests below the cap pass through
    test_rejects_request_over_limit(): verifies the (n+1)th request gets a 429
"""

from types import SimpleNamespace

from starlette.responses import Response

from apps.api.middleware.rate_limit import RateLimitMiddleware


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
