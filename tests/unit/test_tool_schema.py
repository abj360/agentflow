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


def test_round_trip_preserves_name_and_params() -> None:
    """Verifies a spec survives a schema round trip."""
    from agentflow_core.tool_schema import from_mcp_schema

    restored = from_mcp_schema(to_mcp_schema(SPEC))
    assert restored.name == SPEC.name
    assert {p.name for p in restored.parameters} == {"q", "limit"}


def test_round_trip_preserves_required_flags() -> None:
    """Verifies required flags survive a schema round trip."""
    from agentflow_core.tool_schema import from_mcp_schema

    restored = from_mcp_schema(to_mcp_schema(SPEC))
    by_name = {p.name: p for p in restored.parameters}
    assert by_name["q"].required is True
    assert by_name["limit"].required is False


def test_empty_spec_schema_has_no_properties() -> None:
    """Verifies a parameterless tool gets an empty properties map."""
    schema = to_mcp_schema(UnifiedToolSpec(name="ping", description="Ping"))
    assert schema["inputSchema"]["properties"] == {}


def test_spec_is_frozen() -> None:
    """Verifies unified specs are immutable."""
    from dataclasses import FrozenInstanceError

    import pytest

    with pytest.raises(FrozenInstanceError):
        SPEC.name = "other"
