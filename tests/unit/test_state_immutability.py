#!/usr/bin/env python3
"""
test_state_immutability.py --- regression tests for immutable session state

Contains:
    test_snapshot_is_frozen(): verifies snapshots reject attribute mutation
    test_compare_and_swap_conflict_returns_false(): verifies stale writers lose
"""

from dataclasses import FrozenInstanceError

import pytest

from apps.api.orchestration.state import StateSnapshot, StateStore


def test_snapshot_is_frozen() -> None:
    """Verifies snapshots reject attribute mutation."""
    snapshot = StateSnapshot(session_id="s1", version=1)
    with pytest.raises(FrozenInstanceError):
        snapshot.version = 2


def test_compare_and_swap_conflict_returns_false() -> None:
    """Verifies stale writers lose instead of corrupting state."""
    store = StateStore()
    store.advance("s1", plan=("a",))
    stale = StateSnapshot(session_id="s1", version=99)
    assert store.compare_and_swap(0, stale) is False
