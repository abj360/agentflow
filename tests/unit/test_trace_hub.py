#!/usr/bin/env python3
"""
test_trace_hub.py --- unit tests for the trace WebSocket fan-out hub

Contains:
    test_register_adds_connection(): verifies registering tracks the socket
    test_discard_removes_connection(): verifies discarding drops the socket
"""

from apps.api.trace_hub import TraceHub


class FakeSocket:
    """Mimics the WebSocket interface the hub uses."""

    def __init__(self) -> None:
        """Initializes the fake socket."""
        self.accepted = False
        self.sent: list = []

    async def accept(self) -> None:
        """Marks the socket accepted."""
        self.accepted = True

    async def send_json(self, event: dict) -> None:
        """Captures broadcast events."""
        self.sent.append(event)


async def test_register_adds_connection() -> None:
    """Verifies registering tracks the socket."""
    hub = TraceHub()
    socket = FakeSocket()
    await hub.register("run-1", socket)
    assert socket in hub.connections["run-1"]


async def test_discard_removes_connection() -> None:
    """Verifies discarding drops the socket."""
    hub = TraceHub()
    socket = FakeSocket()
    await hub.register("run-1", socket)
    hub.discard("run-1", socket)
    assert hub.connections["run-1"] == set()


async def test_broadcast_sends_to_all_viewers() -> None:
    """Verifies a broadcast reaches every viewer of a run."""
    hub = TraceHub()
    first, second = FakeSocket(), FakeSocket()
    await hub.register("run-1", first)
    await hub.register("run-1", second)
    await hub.broadcast("run-1", {"kind": "plan"})
    assert first.sent == [{"kind": "plan"}]
    assert second.sent == [{"kind": "plan"}]


async def test_broadcast_isolated_per_run() -> None:
    """Verifies broadcasts stay within their run."""
    hub = TraceHub()
    socket = FakeSocket()
    await hub.register("run-2", socket)
    await hub.broadcast("run-1", {"kind": "plan"})
    assert socket.sent == []


async def test_register_accepts_socket() -> None:
    """Verifies registering accepts the socket connection."""
    hub = TraceHub()
    socket = FakeSocket()
    await hub.register("run-1", socket)
    assert socket.accepted is True


async def test_discard_unknown_socket_is_noop() -> None:
    """Verifies discarding an unknown socket does not raise."""
    hub = TraceHub()
    hub.discard("run-1", FakeSocket())


async def test_broadcast_after_discard_skips_socket() -> None:
    """Verifies a discarded viewer stops receiving events."""
    hub = TraceHub()
    socket = FakeSocket()
    await hub.register("run-1", socket)
    hub.discard("run-1", socket)
    await hub.broadcast("run-1", {"kind": "tool_call"})
    assert socket.sent == []
