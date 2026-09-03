#!/usr/bin/env python3
"""
rate_limit.py --- in-memory fixed-window rate limiting middleware

Contains:
    RateLimitMiddleware: caps requests per client within a fixed window
    RedisRateCounter: counts requests in Redis for multi-instance deployments
"""

import time
from typing import Protocol

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

MAX_REQUESTS = 120
WINDOW_SECONDS = 60
EXEMPT_PATHS = frozenset({"/health", "/metrics", "/ready"})
SWEEP_EVERY_REQUESTS = 1024  # amortized cleanup so idle clients cannot leak memory


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Caps requests per client within a fixed window.

    Attributes:
        max_requests: Maximum requests allowed per client per window.
        window_seconds: Length of the fixed rate-limit window.
    """

    def __init__(
        self, app: ASGIApp, max_requests: int = MAX_REQUESTS, window_seconds: int = WINDOW_SECONDS
    ) -> None:
        """Initializes the middleware with limits and the request counter store.

        Args:
            app: The ASGI application being wrapped.
            max_requests: Maximum requests allowed per client per window.
            window_seconds: Length of the fixed rate-limit window.

        Raises:
            ValueError: When the limit or window is not positive.
        """
        super().__init__(app)
        if max_requests <= 0 or window_seconds <= 0:
            raise ValueError("rate limit and window must both be positive")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._counters: dict[str, tuple[float, int]] = {}
        self._now = time.monotonic
        self._requests_since_sweep = 0

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Rejects requests that exceed the per-client window allowance.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            response: The downstream response, or a 429 when over the limit.
        """
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)
        client = self._client_key(request)
        now = self._now()
        self._sweep_expired(now)
        window_start, count = self._counters.get(client, (now, 0))
        if now - window_start > self.window_seconds:
            window_start, count = now, 0
        count += 1
        self._counters[client] = (window_start, count)
        remaining = max(self.max_requests - count, 0)
        if count > self.max_requests:
            return JSONResponse(
                {"detail": "rate limit exceeded", "retry_after": self.window_seconds},
                status_code=429,
            )
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

    def _sweep_expired(self, now: float) -> None:
        """Drops counters whose window has lapsed, bounding memory use.

        Args:
            now: Current monotonic timestamp driving expiry.
        """
        self._requests_since_sweep += 1
        if self._requests_since_sweep < SWEEP_EVERY_REQUESTS:
            return
        self._requests_since_sweep = 0
        cutoff = now - self.window_seconds
        expired = [key for key, (start, _) in self._counters.items() if start <= cutoff]
        for key in expired:
            del self._counters[key]

    def _client_key(self, request: Request) -> str:
        """Resolves the rate-limit key, preferring tenant headers.

        Args:
            request: The incoming HTTP request.

        Returns:
            client_key: Tenant header when present, otherwise the client host.
        """
        tenant = request.headers.get("x-tenant-id")
        if tenant:
            return f"tenant:{tenant}"
        return request.client.host if request.client else "unknown"


class RedisLike(Protocol):
    """Structural interface for the async Redis calls the counter uses."""

    async def incr(self, key: str) -> int:
        """Increments and returns the count for a key.

        Args:
            key: Counter key to increment.

        Returns:
            count: The counter's value after the increment.
        """

    async def expire(self, key: str, seconds: int) -> object:
        """Sets a key expiry in seconds.

        Args:
            key: Key to expire.
            seconds: Time-to-live applied to the key.
        """


class RedisRateCounter:
    """Counts requests in Redis for multi-instance rate limiting.

    Attributes:
        redis: Async Redis client used for INCR/EXPIRE bookkeeping.
        prefix: Key prefix separating rate-limit keys from other data.
    """

    def __init__(self, redis: RedisLike, prefix: str = "ratelimit") -> None:
        """Initializes the counter with a Redis client and key prefix.

        Args:
            redis: Async Redis client used for INCR/EXPIRE bookkeeping.
            prefix: Key prefix separating rate-limit keys from other data.
        """
        self.redis = redis
        self.prefix = prefix

    async def hit(self, client: str, window_seconds: int) -> int:
        """Increments and returns the client's count for the current window.

        Args:
            client: Client identifier the counter is keyed on.
            window_seconds: Length of the fixed rate-limit window.

        Returns:
            count: The client's request count within the current window.
        """
        key = f"{self.prefix}:{client}:{int(window_seconds)}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, window_seconds)
        return count
