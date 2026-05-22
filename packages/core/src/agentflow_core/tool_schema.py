#!/usr/bin/env python3
"""
tool_schema.py --- unified tool schema shared by stdio and SSE transports

Contains:
    ToolParameter: one named argument of a tool
    UnifiedToolSpec: transport-agnostic tool description
    to_mcp_schema(): renders a UnifiedToolSpec as an MCP tool schema
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolParameter:
    """Describes one named argument of a tool.

    Attributes:
        name: Parameter name as it appears in the schema.
        type: JSON Schema type of the parameter.
        description: Human-readable parameter summary.
        required: Whether callers must provide the parameter.
    """

    name: str
    type: str
    description: str = ""
    required: bool = False


@dataclass(frozen=True)
class UnifiedToolSpec:
    """Represents a transport-agnostic tool description.

    Attributes:
        name: Tool name clients call it by.
        description: Human-readable tool summary.
        parameters: Tool arguments in declaration order.
    """

    name: str
    description: str
    parameters: tuple[ToolParameter, ...] = ()


def to_mcp_schema(spec: UnifiedToolSpec) -> dict:
    """Renders a UnifiedToolSpec as an MCP tool schema.

    Args:
        spec: The unified tool description to render.

    Returns:
        schema: MCP-compliant tool schema dict.
    """
    return {
        "name": spec.name,
        "description": spec.description,
        "inputSchema": {
            "type": "object",
            "properties": {
                param.name: {"type": param.type, "description": param.description}
                for param in spec.parameters
            },
            "required": sorted(
                param.name for param in spec.parameters if param.required
            ),
        },
    }


def from_mcp_schema(schema: dict) -> UnifiedToolSpec:
    """Parses an MCP tool schema back into a UnifiedToolSpec.

    Args:
        schema: MCP-compliant tool schema dict.

    Returns:
        spec: The equivalent unified tool description.
    """
    input_schema = schema.get("inputSchema", {})
    required = set(input_schema.get("required", []))
    parameters = tuple(
        ToolParameter(
            name=name,
            type=fields.get("type", "string"),
            description=fields.get("description", ""),
            required=name in required,
        )
        for name, fields in input_schema.get("properties", {}).items()
    )
    return UnifiedToolSpec(
        name=schema["name"],
        description=schema.get("description", ""),
        parameters=parameters,
    )
