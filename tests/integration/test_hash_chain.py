#!/usr/bin/env python3
"""
test_hash_chain.py --- integration tests for the hash-chained audit log

Contains:
    test_chain_links_events_in_order(): verifies each event points at its predecessor
    test_tampering_breaks_verification(): verifies a modified payload is detected
"""

from apps.api.audit.chain import (
    GENESIS_HASH,
    ChainLinker,
    compute_event_hash,
    verify_chain,
)


class FakeEvent:
    """Carries the fields chain verification reads off an audit event."""

    def __init__(
        self, trace_id: str, kind: str, payload: dict, prev_hash: str, event_hash: str
    ) -> None:
        """Stores the chain fields as attributes."""
        self.trace_id = trace_id
        self.kind = kind
        self.payload = payload
        self.prev_hash = prev_hash
        self.event_hash = event_hash


def test_chain_links_events_in_order() -> None:
    """Verifies each event points at its predecessor."""
    linker = ChainLinker()
    prev_1, hash_1 = linker.link("trace-1", "plan_created", {"step": 1})
    prev_2, hash_2 = linker.link("trace-1", "tool_call", {"tool": "search"})
    assert prev_1 == GENESIS_HASH
    assert prev_2 == hash_1
    assert hash_1 != hash_2


def test_tampering_breaks_verification() -> None:
    """Verifies a modified payload is detected."""
    _, hash_1 = ChainLinker().link("trace-1", "plan_created", {"step": 1})
    tampered = compute_event_hash("trace-1", "plan_created", {"step": 2}, GENESIS_HASH)
    assert tampered != hash_1


def test_genesis_hash_is_zero_padded() -> None:
    """Verifies the genesis sentinel is a 64-char zero digest."""
    assert GENESIS_HASH == "0" * 64


def test_linker_isolates_traces() -> None:
    """Verifies events of different traces chain independently."""
    linker = ChainLinker()
    prev_a, _ = linker.link("trace-a", "plan_created", {})
    prev_b, _ = linker.link("trace-b", "plan_created", {})
    assert prev_a == prev_b == GENESIS_HASH


def test_verify_chain_empty_is_valid() -> None:
    """Verifies an empty chain is trivially valid."""
    assert verify_chain([])


def test_compute_event_hash_deterministic() -> None:
    """Verifies identical inputs produce identical hashes."""
    args = ("trace-1", "tool_call", {"a": 1}, GENESIS_HASH)
    assert compute_event_hash(*args) == compute_event_hash(*args)


def test_verify_chain_accepts_untampered_chain() -> None:
    """Verifies a chain produced by the linker passes verification."""
    linker = ChainLinker()
    events = []
    for kind, payload in [("plan_created", {"step": 1}), ("tool_call", {"tool": "x"})]:
        prev_hash, event_hash = linker.link("trace-1", kind, payload)
        events.append(FakeEvent("trace-1", kind, payload, prev_hash, event_hash))
    assert verify_chain(events)


def test_verify_chain_detects_dropped_event() -> None:
    """Verifies removing an event from the middle breaks the chain."""
    linker = ChainLinker()
    events = []
    for idx in range(3):
        prev_hash, event_hash = linker.link("trace-1", "tool_call", {"idx": idx})
        events.append(FakeEvent("trace-1", "tool_call", {"idx": idx}, prev_hash, event_hash))
    del events[1]
    assert not verify_chain(events)
