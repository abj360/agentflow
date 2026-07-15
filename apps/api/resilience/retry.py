#!/usr/bin/env python3
"""
retry.py --- retries calls to downstream MCP servers with backoff and jitter

Contains:
    call_with_retries(): retries a failed downstream call with exponential backoff
    (fixes the thundering-herd tight-loop retry from the initial version)
    backoff_delay(): computes the jittered delay for one retry attempt
"""

import asyncio
import random

BASE_DELAY_SECONDS = 0.1
MAX_DELAY_SECONDS = 5.0


def backoff_delay(attempt: int, base: float = BASE_DELAY_SECONDS) -> float:
    """Computes the jittered delay for one retry attempt.

    Args:
        attempt: Zero-based retry attempt index.
        base: Base delay in seconds doubled per attempt.

    Returns:
        delay: Jittered exponential backoff delay in seconds.
    """
    exponential = min(MAX_DELAY_SECONDS, base * (2**attempt))
    return exponential * random.uniform(0.5, 1.5)


async def call_with_retries(func, max_retries: int = 3):
    """Retries a failed downstream call with exponential backoff.

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
            await asyncio.sleep(backoff_delay(attempt - 1))
