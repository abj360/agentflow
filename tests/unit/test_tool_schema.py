#!/usr/bin/env python3
"""
test_tool_schema.py --- unit tests for the unified cross-transport tool schema

Contains:
    test_to_mcp_schema_renders_name(): verifies the schema carries the tool name
    test_required_params_listed(): verifies required params land in required
"""

from agentflow_core.tool_schema import ToolParameter, UnifiedToolSpec, to_mcp_schema

SPEC = UnifiedToolSpec(
    name="search.query",
    description="Run a search query",
    parameters=(
        ToolParameter(name="q", type="string", description="Query text",
                      required=True),
        ToolParameter(name="limit", type="integer"),
    ),
)


def test_to_mcp_schema_renders_name() -> None:
    """Verifies the schema carries the tool name."""
    assert to_mcp_schema(SPEC)["name"] == "search.query"


def test_required_params_listed() -> None:
    """Verifies required params land in required."""
    schema = to_mcp_schema(SPEC)
    assert schema["inputSchema"]["required"] == ["q"]


def test_optional_params_not_required() -> None:
    """Verifies optional params stay out of required."""
    schema = to_mcp_schema(SPEC)
    assert "limit" not in schema["inputSchema"]["required"]
