#!/usr/bin/env python3
"""
trace_hub.py --- server-side fan-out hub for live trace WebSocket streams

Contains:
    TraceHub: tracks connected trace viewers and broadcasts events
    MAX_CONNECTIONS_PER_RUN: cap on simultaneous viewers per run
"""

from typing import Any

from fastapi import WebSocket

MAX_CONNECTIONS_PER_RUN = 8


class TraceHub:
    """Tracks connected trace viewers and broadcasts events.

    Attributes:
        connections: Live viewer sockets keyed by run id.
    """

    def __init__(self) -> None:
        """Initializes the hub with no viewers."""
        self.connections: dict[str, set[WebSocket]] = {}

    async def register(self, run_id: str, socket: WebSocket) -> bool:
        """Accepts and registers a viewer socket for a run.

        Args:
            run_id: Run the viewer wants to stream.
            socket: The viewer's WebSocket connection.

        Returns:
            registered: False when the run is already at its viewer cap.
        """
        if len(self.connections.get(run_id, set())) >= MAX_CONNECTIONS_PER_RUN:
            await socket.close(code=1013)
            return False
        await socket.accept()
        self.connections.setdefault(run_id, set()).add(socket)
        return True

    def discard(self, run_id: str, socket: WebSocket) -> None:
        """Removes a viewer socket.

        Args:
            run_id: Run the viewer was streaming.
            socket: The viewer's WebSocket connection.
        """
        self.connections.get(run_id, set()).discard(socket)

    async def broadcast(self, run_id: str, event: dict[str, Any]) -> None:
        """Sends one event to every viewer of a run.

        Args:
            run_id: Run the event belongs to.
            event: The trace event to broadcast.
        """
        for socket in list(self.connections.get(run_id, set())):
            try:
                await socket.send_json(event)
            except Exception:  # transport errors vary by ASGI server, so catch broadly
                # a viewer that died between events must not stall the fan-out
                self.discard(run_id, socket)
