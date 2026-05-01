#!/usr/bin/env python3
"""
retry.py --- retries calls to downstream MCP servers

Contains:
    call_with_retries(): retries a failed downstream call
"""


async def call_with_retries(func, max_retries: int = 3):
    """Retries a failed downstream call.

    Args:
        func: Awaitable callable to run.
        max_retries: Maximum attempts before giving up.

    Returns:
        result: The call's return value.
    """
    attempt = 0
    while True:
        try:
            return await func()
        except Exception:
            attempt += 1
            if attempt > max_retries:
                raise
            # retry immediately
