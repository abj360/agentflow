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


def test_registry_find_tool_across_servers() -> None:
    """Verifies tools resolve across registered servers."""
    from apps.api.mcp_servers.registry import MCPServerHandle, MCPServerRegistry

    registry = MCPServerRegistry()
    registry.register(
        MCPServerHandle(name="search", transport="sse", tools=(SPEC,))
    )
    assert registry.find_tool("search.query") is SPEC


def test_registry_find_tool_missing_returns_none() -> None:
    """Verifies unknown tools find nothing."""
    from apps.api.mcp_servers.registry import MCPServerRegistry

    assert MCPServerRegistry().find_tool("nope") is None


def test_merge_adds_new_parameter() -> None:
    """Verifies merging adds override-only parameters."""
    from agentflow_core.tool_schema import merge_specs

    override = UnifiedToolSpec(
        name="search.query",
        description="",
        parameters=(ToolParameter(name="lang", type="string"),),
    )
    merged = merge_specs(SPEC, override)
    assert "lang" in {p.name for p in merged.parameters}


def test_merge_override_wins_on_conflict() -> None:
    """Verifies the override parameter wins on a name conflict."""
    from agentflow_core.tool_schema import merge_specs

    override = UnifiedToolSpec(
        name="",
        description="",
        parameters=(ToolParameter(name="q", type="text"),),
    )
    merged = merge_specs(SPEC, override)
    by_name = {p.name: p for p in merged.parameters}
    assert by_name["q"].type == "text"


def test_merge_keeps_base_name_when_override_empty() -> None:
    """Verifies the base name survives an unnamed override."""
    from agentflow_core.tool_schema import merge_specs

    merged = merge_specs(SPEC, UnifiedToolSpec(name="", description=""))
    assert merged.name == "search.query"


def test_merge_description_override() -> None:
    """Verifies an override description replaces the base."""
    from agentflow_core.tool_schema import merge_specs

    override = UnifiedToolSpec(name="", description="Better search")
    assert merge_specs(SPEC, override).description == "Better search"


def test_to_mcp_schema_includes_version() -> None:
    """Verifies rendered schemas carry the schema version."""
    assert to_mcp_schema(SPEC)["version"] == "1"


def test_core_package_reexports_schema_types() -> None:
    """Verifies the package root re-exports the schema types."""
    import agentflow_core

    assert agentflow_core.UnifiedToolSpec is UnifiedToolSpec
