#!/usr/bin/env python3
"""
registry.py --- registry of MCP servers keyed by transport

Contains:
    MCPServerHandle: one registered MCP server and its transport
    MCPServerRegistry: tracks registered servers across transports
"""

from dataclasses import dataclass

from agentflow_core.tool_schema import UnifiedToolSpec


@dataclass(frozen=True)
class MCPServerHandle:
    """Represents one registered MCP server and its transport.

    Attributes:
        name: Server name used for routing tool calls.
        transport: Transport the server speaks: stdio or sse.
        tools: Tools the server exposes in unified form.
    """

    name: str
    transport: str
    tools: tuple[UnifiedToolSpec, ...] = ()


class MCPServerRegistry:
    """Tracks registered servers across transports.

    Attributes:
        servers: Registered server handles keyed by server name.
    """

    def __init__(self) -> None:
        """Initializes an empty registry."""
        self.servers: dict[str, MCPServerHandle] = {}

    def register(self, handle: MCPServerHandle) -> None:
        """Registers a server handle.

        Args:
            handle: The server handle to register.
        """
        self.servers[handle.name] = handle

    def resolve(self, name: str) -> MCPServerHandle | None:
        """Looks up a server handle by name.

        Args:
            name: Server name to resolve.

        Returns:
            handle: The server handle, or None when unknown.
        """
        return self.servers.get(name)

    def find_tool(self, tool_name: str) -> UnifiedToolSpec | None:
        """Finds a tool across every registered server.

        Args:
            tool_name: Tool name to look up.

        Returns:
            spec: The unified tool spec, or None when no server exposes it.
        """
        for handle in self.servers.values():
            for spec in handle.tools:
                if spec.name == tool_name:
                    return spec
        return None
