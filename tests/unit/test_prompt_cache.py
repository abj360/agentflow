#!/usr/bin/env python3
"""
test_prompt_cache.py --- unit tests for the planner prompt cache

Contains:
    test_cache_key_stable(): verifies identical inputs produce identical keys
    test_put_then_get_returns_completion(): verifies a stored completion reads back
"""

from apps.api.orchestration.prompt_cache import PromptCache, cache_key


def test_cache_key_stable() -> None:
    """Verifies identical inputs produce identical keys."""
    assert cache_key("t", {"a": 1}) == cache_key("t", {"a": 1})


def test_put_then_get_returns_completion() -> None:
    """Verifies a stored completion reads back."""
    cache = PromptCache()
    key = cache_key("t", {})
    cache.put(key, "plan draft")
    assert cache.get(key) == "plan draft"


def test_cache_key_differs_on_context() -> None:
    """Verifies different contexts hash to different keys."""
    assert cache_key("t", {"a": 1}) != cache_key("t", {"a": 2})


def test_get_missing_key_returns_none() -> None:
    """Verifies a cache miss returns None."""
    assert PromptCache().get("nope") is None


def test_cache_key_is_hex_digest() -> None:
    """Verifies keys are hex-encoded digests."""
    key = cache_key("task", {})
    int(key, 16)
    assert len(key) == 64


def test_put_overwrites_existing_entry() -> None:
    """Verifies re-putting a key replaces the completion."""
    cache = PromptCache()
    cache.put("k", "first")
    cache.put("k", "second")
    assert cache.get("k") == "second"


def test_get_returns_latest_completion() -> None:
    """Verifies get returns the most recently stored completion."""
    cache = PromptCache()
    cache.put("k", "newer")
    assert cache.get("k") == "newer"


def test_cache_key_differs_on_task() -> None:
    """Verifies different tasks hash to different keys."""
    assert cache_key("task-a", {}) != cache_key("task-b", {})


def test_get_fresh_returns_value_within_ttl() -> None:
    """Verifies a fresh entry reads back within its TTL."""
    cache = PromptCache()
    cache.put("k", "v")
    assert cache.get_fresh("k", ttl_seconds=60) == "v"


def test_get_fresh_misses_unknown_key() -> None:
    """Verifies get_fresh misses for unknown keys."""
    assert PromptCache().get_fresh("nope", ttl_seconds=60) is None
