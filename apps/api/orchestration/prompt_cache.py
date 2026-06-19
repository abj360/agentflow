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

    def __init__(self, max_entries: int = 512) -> None:
        """Initializes an empty cache.

        Args:
            max_entries: Maximum cached completions before LRU eviction.
        """
        self.max_entries = max_entries
        self.entries: dict[str, tuple[str, float]] = {}
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key: str) -> str | None:
        """Looks up a cached completion.

        Args:
            key: Content hash produced by cache_key.

        Returns:
            completion: The cached completion, or None on a miss.
        """
        entry = self.entries.get(key)
        if entry is None:
            self.misses += 1
            return None
        self.hits += 1
        return entry[0]

    def put(self, key: str, completion: str) -> None:
        """Stores a completion under its content hash.

        Args:
            key: Content hash produced by cache_key.
            completion: The planner completion to cache.
        """
        if len(self.entries) >= self.max_entries:
            oldest = min(
                self.entries, key=lambda entry_key: self.entries[entry_key][1]
            )
            del self.entries[oldest]
        self.entries[key] = (completion, time.time())


    def get_fresh(self, key: str, ttl_seconds: float) -> str | None:
        """Looks up a cached completion, honoring a time-to-live.

        Args:
            key: Content hash produced by cache_key.
            ttl_seconds: Maximum age of a usable cache entry.

        Returns:
            completion: The cached completion, or None when missing or stale.
        """
        entry = self.entries.get(key)
        if entry is None:
            return None
        value, stored_at = entry
        age = time.time() - stored_at
        if age > ttl_seconds:
            del self.entries[key]
            return None
        return value
