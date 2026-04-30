#!/usr/bin/env python3
"""
chain.py --- hash-chaining for the append-only audit log

Contains:
    GENESIS_HASH: sentinel hash used as prev_hash for the first event of a trace
    compute_event_hash(): derives a SHA-256 hash over event content and the previous hash
    ChainLinker: tracks the latest hash per trace for chaining new events
"""

import hashlib
import json

GENESIS_HASH = "0" * 64


def compute_event_hash(trace_id: str, kind: str, payload: dict, prev_hash: str) -> str:
    """Derives a SHA-256 hash over event content and the previous hash.

    Args:
        trace_id: Identifier of the orchestration run being recorded.
        kind: Category of the event being recorded.
        payload: Event-specific structured data.
        prev_hash: Hash of the preceding event in the same trace chain.

    Returns:
        event_hash: Hex-encoded SHA-256 digest chaining this event to the previous one.
    """
    canonical = json.dumps(
        {"trace_id": trace_id, "kind": kind, "payload": payload, "prev_hash": prev_hash},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ChainLinker:
    """Tracks the latest hash per trace for chaining new events.

    Attributes:
        last_hashes: Mapping of trace_id to the most recent event hash.
    """

    def __init__(self) -> None:
        """Initializes the linker with no known traces."""
        self.last_hashes: dict[str, str] = {}

    def link(self, trace_id: str, kind: str, payload: dict) -> tuple[str, str]:
        """Computes prev_hash and event_hash for the next event of a trace.

        Args:
            trace_id: Identifier of the orchestration run being recorded.
            kind: Category of the event being recorded.
            payload: Event-specific structured data.

        Returns:
            chain_links: Tuple of (prev_hash, event_hash) for the new event.
        """
        prev_hash = self.last_hashes.get(trace_id, GENESIS_HASH)
        event_hash = compute_event_hash(trace_id, kind, payload, prev_hash)
        self.last_hashes[trace_id] = event_hash
        return prev_hash, event_hash
