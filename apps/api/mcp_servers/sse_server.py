#!/usr/bin/env python3
"""
sse_server.py --- MCP server exposed over Server-Sent Events transport

Contains:
    ToolSpec: describes one tool exposed by the MCP server
    ToolRegistry: tools this server exposes to MCP clients
    default_registry(): builds the registry with the built-in demo tools
    validate_tool_spec(): checks a tool spec for required fields
    create_sse_app(): builds the SSE transport application wiring
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
    version: str = "1.0"

    def mcp_schema(self) -> dict:
        """Renders this spec as an MCP tool schema.

        Returns:
            schema: MCP-compliant tool schema dict.
        """
        unified = UnifiedToolSpec(
            name=self.name,
            description=self.description,
        )
        schema = to_mcp_schema(unified)
        schema["inputSchema"] = self.input_schema
        return schema


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

        Raises:
            ValueError: When the spec fails validation.
        """
        problems = validate_tool_spec(spec)
        if problems:
            raise ValueError(f"invalid tool spec: {problems}")
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

    def unregister(self, name: str) -> bool:
        """Removes a tool from the registry.

        Args:
            name: Tool name to remove.

        Returns:
            removed: True when the tool was present and removed.
        """
        return self.tools.pop(name, None) is not None


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


def validate_tool_spec(spec: ToolSpec) -> list[str]:
    """Checks a tool spec for required fields.

    Args:
        spec: The tool spec to validate.

    Returns:
        problems: Validation problems found, empty when valid.
    """
    problems = []
    if not spec.name:
        problems.append("tool name is required")
    if not spec.description:
        problems.append(f"{spec.name}: description is required")
    return problems


def create_sse_app(registry: ToolRegistry) -> dict:
    """Builds the SSE transport application wiring.

    Args:
        registry: Tool registry whose tools the transport serves.

    Returns:
        app: ASGI app descriptor for the SSE endpoint.
    """
    return {"transport": "sse", "tools": [spec.name for spec in registry.list_tools()]}
