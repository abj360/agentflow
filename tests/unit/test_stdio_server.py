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
    response = server.handle_request({"method": "bogus/method"})
    assert "unknown method" in response["error"]


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


def test_tools_call_returns_not_implemented() -> None:
    """Verifies tools/call reports not_implemented for now."""
    response = build_server().handle_request({"method": "tools/call"})
    assert response["result"]["status"] == "not_implemented"


def test_missing_method_returns_error() -> None:
    """Verifies a request without a method gets a clean error."""
    server = build_server()
    assert "error" in server.handle_request({})


def test_build_default_server_has_fs_read() -> None:
    """Verifies the default server ships fs.read."""
    from apps.api.mcp_servers.stdio_server import build_default_server

    server = build_default_server()
    assert "fs.read" in server.list_tools()


def test_default_server_fs_read_schema_requires_path() -> None:
    """Verifies the fs.read tool declares its path argument."""
    from apps.api.mcp_servers.stdio_server import build_default_server

    spec = build_default_server().tools["fs.read"]
    assert "path" in spec.input_schema["properties"]


def test_default_server_has_search_tool() -> None:
    """Verifies the default server also ships search.query."""
    from apps.api.mcp_servers.stdio_server import build_default_server

    assert "search.query" in build_default_server().list_tools()


def test_tools_list_shape_is_mcp_schema() -> None:
    """Verifies the tools/list payload carries MCP schema fields."""
    response = build_server().handle_request({"method": "tools/list"})
    tool = response["tools"][0]
    assert "inputSchema" in tool
