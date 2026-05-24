#!/usr/bin/env python3
"""
sse_server.py --- MCP server exposed over Server-Sent Events transport

Contains:
    ToolSpec: describes one tool exposed by the MCP server
    ToolRegistry: tools this server exposes to MCP clients
    default_registry(): builds the registry with the built-in demo tools
"""

from dataclasses import dataclass, field

from agentflow_core.tool_schema import UnifiedToolSpec, to_mcp_schema


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

    def mcp_schema(self) -> dict:
        """Renders this spec as an MCP tool schema.

        Returns:
            schema: MCP-compliant tool schema dict.
        """
        return self.input_schema


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
        return sorted(self.tools.values(), key=lambda spec: spec.name)

    def get_tool(self, name: str) -> ToolSpec | None:
        """Looks up one registered tool spec.

        Args:
            name: Tool name to look up.

        Returns:
            spec: The tool spec, or None when not registered.
        """
        return self.tools.get(name)


def default_registry() -> ToolRegistry:
    """Builds the registry with the built-in demo tools.

    Returns:
        registry: Tool registry preloaded with the default tool set.
    """
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="search.query",
            description="Runs a search query and returns ranked results",
            input_schema={
                "type": "object",
                "properties": {"q": {"type": "string"}},
                "required": ["q"],
            },
        )
    )
    return registry
