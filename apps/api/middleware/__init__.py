#!/usr/bin/env python3
"""
__init__.py --- public surface of the middleware package

Contains:
    re-exports of middleware components for app wiring
"""

from apps.api.middleware.rate_limit import RateLimitMiddleware

__all__ = ["RateLimitMiddleware"]
