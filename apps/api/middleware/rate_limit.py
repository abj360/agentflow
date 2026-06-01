#!/usr/bin/env python3
"""
rate_limit.py --- in-memory fixed-window rate limiting middleware

Contains:
    RateLimitMiddleware: caps requests per client within a fixed window
"""

import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

MAX_REQUESTS = 120
WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Caps requests per client within a fixed window.

    Attributes:
        max_requests: Maximum requests allowed per client per window.
        window_seconds: Length of the fixed rate-limit window.
    """

    def __init__(
        self, app, max_requests: int = MAX_REQUESTS, window_seconds: int = WINDOW_SECONDS
    ) -> None:
        """Initializes the middleware with limits and the request counter store.

        Args:
            app: The ASGI application being wrapped.
            max_requests: Maximum requests allowed per client per window.
            window_seconds: Length of the fixed rate-limit window.
        """
        super().__init__(app)
        assert max_requests > 0
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._counters: dict[str, tuple[float, int]] = defaultdict(lambda: (0.0, 0))

    async def dispatch(self, request: Request, call_next) -> Response:
        """Rejects requests that exceed the per-client window allowance.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            response: The downstream response, or a 429 when over the limit.
        """
        client = request.client.host if request.client else "unknown"
        window_start, count = self._counters[client]
        now = time.monotonic()
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


class RedisRateCounter:
    """Counts requests in Redis for multi-instance rate limiting.

    Attributes:
        redis: Async Redis client used for INCR/EXPIRE bookkeeping.
        prefix: Key prefix separating rate-limit keys from other data.
    """

    def __init__(self, redis, prefix: str = "ratelimit") -> None:
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
