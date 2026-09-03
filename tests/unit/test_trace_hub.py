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

    async def close(self, code: int = 1000) -> None:
        """Records the close code."""
        self.closed_code = code


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
    assert socket not in hub.connections.get("run-1", set())


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


async def test_register_over_cap_closes_socket() -> None:
    """Verifies viewers beyond the per-run cap get closed, not accepted."""
    from apps.api.trace_hub import MAX_CONNECTIONS_PER_RUN

    hub = TraceHub()
    for _ in range(MAX_CONNECTIONS_PER_RUN):
        await hub.register("run-1", FakeSocket())
    overflow = FakeSocket()
    await hub.register("run-1", overflow)
    assert overflow.closed_code == 1013
    assert overflow not in hub.connections["run-1"]


async def test_register_under_cap_still_accepted() -> None:
    """Verifies viewers under the cap still connect normally."""
    hub = TraceHub()
    socket = FakeSocket()
    await hub.register("run-1", socket)
    assert socket.accepted is True
    assert socket in hub.connections["run-1"]


async def test_multiple_runs_have_separate_connection_sets() -> None:
    """Verifies connections are grouped per run id."""
    hub = TraceHub()
    socket_a, socket_b = FakeSocket(), FakeSocket()
    await hub.register("run-a", socket_a)
    await hub.register("run-b", socket_b)
    assert set(hub.connections) == {"run-a", "run-b"}


async def test_hub_starts_with_no_connections() -> None:
    """Verifies a fresh hub has no viewers."""
    hub = TraceHub()
    assert hub.connections == {}


async def test_run_entry_dropped_when_last_viewer_leaves() -> None:
    """Verifies a run leaves no empty entry behind once its viewers go.

    The hub used to keep an empty set per run id forever, so a long-lived
    process accumulated one entry for every run ever streamed.
    """
    hub = TraceHub()
    socket = FakeSocket()
    await hub.register("run-1", socket)
    hub.discard("run-1", socket)
    assert hub.connections == {}


async def test_discard_unknown_run_is_a_noop() -> None:
    """Verifies discarding a socket for an unknown run does not raise."""
    hub = TraceHub()
    hub.discard("never-seen", FakeSocket())
    assert hub.connections == {}


async def test_other_viewers_survive_a_discard() -> None:
    """Verifies dropping one viewer keeps the run's remaining viewers."""
    hub = TraceHub()
    staying, leaving = FakeSocket(), FakeSocket()
    await hub.register("run-1", staying)
    await hub.register("run-1", leaving)
    hub.discard("run-1", leaving)
    assert hub.connections["run-1"] == {staying}
