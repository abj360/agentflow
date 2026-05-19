#!/usr/bin/env python3
"""
prompt_cache.py --- caches planner prompts to cut round-trip latency

Contains:
    cache_key(): derives a stable cache key from task and context
    PromptCache: stores planner completions keyed by content hash
"""

import hashlib
import json
import time


def cache_key(task: str, context: dict) -> str:
    """Derives a stable cache key from task and context.

    Args:
        task: The planner's input task.
        context: Extra planner context affecting the completion.

    Returns:
        key: Hex-encoded content hash used as the cache key.
    """
    canonical = json.dumps(
        {"task": task, "context": context}, sort_keys=True, default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class PromptCache:
    """Stores planner completions keyed by content hash.

    Attributes:
        entries: Cached completions plus store timestamps keyed by content hash.
    """

    def __init__(self) -> None:
        """Initializes an empty cache."""
        self.entries: dict[str, tuple[str, float]] = {}

    def get(self, key: str) -> str | None:
        """Looks up a cached completion.

        Args:
            key: Content hash produced by cache_key.

        Returns:
            completion: The cached completion, or None on a miss.
        """
        entry = self.entries.get(key)
        return entry[0] if entry else None

    def put(self, key: str, completion: str) -> None:
        """Stores a completion under its content hash.

        Args:
            key: Content hash produced by cache_key.
            completion: The planner completion to cache.
        """
        self.entries[key] = (completion, time.time())
