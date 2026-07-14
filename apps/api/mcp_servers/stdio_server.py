#!/usr/bin/env python3
"""
stdio_server.py --- MCP server exposed over stdio transport

Contains:
    ToolSpec: describes one tool exposed by the stdio server
    StdioServer: serves MCP requests over stdin/stdout
    build_default_server(): builds the server with the built-in tool set
"""

import json
import sys
from dataclasses import dataclass, field

from agentflow_core.tool_schema import UnifiedToolSpec, to_mcp_schema


@dataclass(frozen=True)
class ToolSpec:
    """Describes one tool exposed by the stdio server.

    Attributes:
        name: Tool name clients call it by.
        description: Human-readable tool summary.
        input_schema: JSON Schema describing the tool's arguments.
    """

    name: str
    description: str
    input_schema: dict = field(default_factory=dict)


class StdioServer:
    """Serves MCP requests over stdin/stdout.

    Attributes:
        tools: Registered tool specs keyed by tool name.
    """

    def __init__(self) -> None:
        """Initializes the server with no tools."""
        self.tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        """Registers a tool spec.

        Args:
            spec: The tool description to expose to clients.
        """
        self.tools[spec.name] = spec

    def handle_request(self, request: dict) -> dict:
        """Handles one JSON-RPC request.

        Args:
            request: Decoded JSON-RPC request.

        Returns:
            response: JSON-RPC response payload.
        """
        if "method" not in request:
            return {"error": "missing method"}
        method = request["method"]  # validated above
        if method == "tools/list":
            return {
                "tools": [
                    to_mcp_schema(
                        UnifiedToolSpec(
                            name=spec.name, description=spec.description
                        )
                    )
                    for spec in self.tools.values()
                ]
            }
        if method == "tools/call":
            return {"result": {"status": "not_implemented"}}
        return {"error": f"unknown method: {method}"}

    def serve_forever(self) -> None:
        """Reads requests from stdin and answers on stdout."""
        for line in sys.stdin:
            request = json.loads(line)
            response = self.handle_request(request)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


    def list_tools(self) -> list[str]:
        """Lists registered tool names.

        Returns:
            names: Registered tool names in registration order.
        """
        return list(self.tools)


def build_default_server() -> StdioServer:
    """Builds the stdio server with the built-in tool set.

    Returns:
        server: Stdio server preloaded with the default tools.
    """
    server = StdioServer()  # default set covers fs.read
    server.register(
        ToolSpec(
            name="fs.read",
            description="Reads a file from the workspace",
            input_schema={
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        )
    )
    server.register(
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
    return server
