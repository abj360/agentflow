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


def test_validate_accepts_valid_spec() -> None:
    """Verifies a complete spec passes validation."""
    from agentflow_core.tool_schema import validate_unified_spec

    assert validate_unified_spec(SPEC) == []


def test_validate_flags_missing_name() -> None:
    """Verifies a spec without a name fails validation."""
    from agentflow_core.tool_schema import validate_unified_spec

    problems = validate_unified_spec(
        UnifiedToolSpec(name="", description="d")
    )
    assert "tool name is required" in problems


def test_registry_register_and_resolve() -> None:
    """Verifies servers register and resolve by name."""
    from apps.api.mcp_servers.registry import MCPServerHandle, MCPServerRegistry

    registry = MCPServerRegistry()
    registry.register(MCPServerHandle(name="search", transport="sse"))
    assert registry.resolve("search") is not None


def test_registry_resolve_missing_returns_none() -> None:
    """Verifies unknown servers resolve to None."""
    from apps.api.mcp_servers.registry import MCPServerRegistry

    assert MCPServerRegistry().resolve("ghost") is None
