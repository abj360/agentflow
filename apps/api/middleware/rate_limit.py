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
        if count > self.max_requests:
            return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        return await call_next(request)
