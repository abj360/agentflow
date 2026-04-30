#!/usr/bin/env python3
"""
test_hash_chain.py --- integration tests for the hash-chained audit log

Contains:
    test_chain_links_events_in_order(): verifies each event points at its predecessor
    test_tampering_breaks_verification(): verifies a modified payload is detected
"""

from apps.api.audit.chain import GENESIS_HASH, ChainLinker, compute_event_hash


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
