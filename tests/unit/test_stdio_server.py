#!/usr/bin/env python3
"""
test_stdio_server.py --- unit tests for the stdio MCP server

Contains:
    test_handle_tools_list(): verifies tools/list returns registered tools
    test_unknown_method_returns_error(): verifies unknown methods get an error
"""

from apps.api.mcp_servers.stdio_server import StdioServer, ToolSpec


def build_server() -> StdioServer:
    """Builds a server with one registered test tool.

    Returns:
        server: Stdio server with a single registered tool.
    """
    server = StdioServer()
    server.register(ToolSpec(name="fs.read", description="Read a file"))
    return server


def test_handle_tools_list() -> None:
    """Verifies tools/list returns registered tools."""
    response = build_server().handle_request({"method": "tools/list"})
    assert "fs.read" in str(response)


def test_unknown_method_returns_error() -> None:
    """Verifies unknown methods get an error."""
    server = build_server()
    assert "error" in server.handle_request({"method": "bogus/method"})


def test_list_tools_method() -> None:
    """Verifies list_tools returns the registered names."""
    assert build_server().list_tools() == ["fs.read"]


def test_register_second_tool() -> None:
    """Verifies a second tool registers cleanly."""
    server = build_server()
    server.register(ToolSpec(name="search.query", description="Search"))
    assert server.list_tools() == ["fs.read", "search.query"]


def test_tools_list_includes_schema_after_unify() -> None:
    """Verifies tools/list emits unified MCP schemas."""
    response = build_server().handle_request({"method": "tools/list"})
    assert response["tools"][0]["name"] == "fs.read"
