#!/usr/bin/env python3
"""
test_sse_server.py --- unit tests for the SSE MCP server scaffolding

Contains:
    test_register_and_list_tools(): verifies registration is reflected in listing
    test_list_tools_empty_registry(): verifies an empty registry lists nothing
"""

from apps.api.mcp_servers.sse_server import ToolRegistry, ToolSpec


def test_register_and_list_tools() -> None:
    """Verifies registration is reflected in listing."""
    registry = ToolRegistry()
    registry.register(ToolSpec(name="search.query", description="Search"))
    assert [spec.name for spec in registry.list_tools()] == ["search.query"]


def test_list_tools_empty_registry() -> None:
    """Verifies an empty registry lists nothing."""
    assert ToolRegistry().list_tools() == []


def test_register_overwrites_same_name() -> None:
    """Verifies re-registering a name replaces the spec."""
    registry = ToolRegistry()
    registry.register(ToolSpec(name="t", description="first"))
    registry.register(ToolSpec(name="t", description="second"))
    assert registry.list_tools()[0].description == "second"


def test_default_registry_has_search_tool() -> None:
    """Verifies the default registry ships the search tool."""
    from apps.api.mcp_servers.sse_server import default_registry

    registry = default_registry()
    assert "search.query" in registry.tools


def test_default_search_tool_schema_requires_query() -> None:
    """Verifies the search tool declares its query argument."""
    from apps.api.mcp_servers.sse_server import default_registry

    spec = default_registry().tools["search.query"]
    assert "q" in spec.input_schema["properties"]


def test_get_tool_returns_spec() -> None:
    """Verifies get_tool returns the registered spec."""
    registry = ToolRegistry()
    registry.register(ToolSpec(name="fs.read", description="Read a file"))
    assert registry.get_tool("fs.read") is not None


def test_get_tool_missing_returns_none() -> None:
    """Verifies get_tool misses cleanly for unknown tools."""
    assert ToolRegistry().get_tool("nope") is None
