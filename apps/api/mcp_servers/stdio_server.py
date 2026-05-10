#!/usr/bin/env python3
"""
stdio_server.py --- MCP server exposed over stdio transport

Contains:
    ToolSpec: describes one tool exposed by the stdio server
    StdioServer: serves MCP requests over stdin/stdout
"""

import json
import sys
from dataclasses import dataclass, field


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
        method = request.get("method")
        if method == "tools/list":
            return {"tools": [spec.name for spec in self.tools.values()]}
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
