#!/usr/bin/env python3
"""
sse_server.py --- MCP server exposed over Server-Sent Events transport

Contains:
    ToolSpec: describes one tool exposed by the MCP server
    ToolRegistry: tools this server exposes to MCP clients
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolSpec:
    """Describes one tool exposed by the MCP server.

    Attributes:
        name: Tool name clients call it by.
        description: Human-readable tool summary.
        input_schema: JSON Schema describing the tool's arguments.
    """

    name: str
    description: str
    input_schema: dict = field(default_factory=dict)


class ToolRegistry:
    """Tools this server exposes to MCP clients.

    Attributes:
        tools: Registered tool specs keyed by tool name.
    """

    def __init__(self) -> None:
        """Initializes an empty registry."""
        self.tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        """Registers a tool spec.

        Args:
            spec: The tool description to expose to clients.
        """
        self.tools[spec.name] = spec

    def list_tools(self) -> list[ToolSpec]:
        """Lists every registered tool spec.

        Returns:
            specs: All registered tool specs in registration order.
        """
        return list(self.tools.values())
