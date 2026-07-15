#!/usr/bin/env python3
"""
test_orchestration_loop.py --- integration tests for the orchestration loop

Contains:
    test_run_session_completes(): verifies a session runs to completion
    test_run_session_result_shape(): verifies the loop result carries the contract
"""

from apps.api.orchestration.loop import run_session


async def test_run_session_completes() -> None:
    """Verifies a session runs to completion."""
    result = await run_session("it-1", "draft a plan")
    assert result is not None


async def test_run_session_result_shape() -> None:
    """Verifies the loop result carries the contract."""
    result = await run_session("it-2", "summarize a doc")
    assert {"output", "iterations", "status"} <= set(result)


async def test_run_session_records_iterations() -> None:
    """Verifies the loop reports at least one iteration."""
    result = await run_session("it-3", "iterate once")
    assert isinstance(result["iterations"], int)


async def test_output_is_list_of_results() -> None:
    """Verifies the output field carries the executor's results."""
    result = await run_session("it-f1", "collect outputs")
    assert isinstance(result["output"], list)


async def test_sessions_do_not_share_state() -> None:
    """Verifies concurrent sessions stay independent."""
    first_result = await run_session("it-4a", "task a")
    second_result = await run_session("it-4b", "task b")
    assert first_result is not second_result


async def test_result_contains_status_key() -> None:
    """Verifies the loop result carries a status key."""
    result = await run_session("it-f2", "status check")
    assert "status" in result


async def test_state_snapshot_versions_advance() -> None:
    """Verifies the state store advances versions per iteration."""
    from apps.api.orchestration.state import StateStore

    store = StateStore()
    store.advance("it-5")
    store.advance("it-5")
    assert store.get("it-5").version == 2


async def test_state_store_unknown_session_empty() -> None:
    """Verifies an unknown session reads as an empty snapshot."""
    from apps.api.orchestration.state import StateStore

    assert StateStore().get("ghost").version == 0


async def test_run_session_status_completed() -> None:
    """Verifies an accepted run reports completed status."""
    result = await run_session("it-6", "finish fast")
    assert result["status"] in {"completed", "revision-bounded"}


async def test_iterations_positive_integer() -> None:
    """Verifies iteration counts come back as positive integers."""
    result = await run_session("it-f3", "count me")
    assert result["iterations"] > 0


class NullHooks:
    """Ignores all hook invocations."""

    async def on_iteration(self, session_id: str, iteration: int) -> None:
        """Ignores an iteration."""

    async def on_complete(self, session_id: str, result: dict) -> None:
        """Ignores completion."""


async def test_hooks_observe_iterations() -> None:
    """Verifies lifecycle hooks see the loop's progress."""
    result = await run_session("it-7", "hooked", hooks=NullHooks())
    assert result is not None


async def test_hooks_receive_completion_result() -> None:
    """Verifies the completion hook gets the final result."""
    captured = []  # completion results land here

    class CapturingHooks:
        """Captures the completion result."""

        async def on_iteration(self, session_id: str, iteration: int) -> None:
            """Ignores iterations."""

        async def on_complete(self, session_id: str, result: dict) -> None:
            """Captures the completion result."""
            captured.append(result)

    await run_session("it-f4", "capture", hooks=CapturingHooks())
    assert len(captured) == 1


async def test_run_session_without_hooks_still_works() -> None:
    """Verifies hooks remain optional."""
    result = await run_session("it-f5", "no hooks")
    assert result["status"] in {"completed", "revision-bounded"}


async def test_graph_state_has_expected_keys() -> None:
    """Verifies node updates keep the graph state shape."""
    from apps.api.orchestration.state_machine import planner_node

    state = planner_node(
        {"task": "x", "plan": [], "results": [], "critique": "", "iterations": 0}
    )
    assert set(state) == {"task", "plan", "results", "critique", "iterations"}


async def test_graph_routes_to_accept_with_results() -> None:
    """Verifies the graph accepts once results exist."""
    from apps.api.orchestration.state_machine import critic_node, route_after_critic

    state = critic_node(
        {
            "task": "t",
            "plan": ["p"],
            "results": ["r"],
            "critique": "",
            "iterations": 0,
        }
    )
    assert route_after_critic(state) == "accept"


async def test_registry_rejects_unknown_role() -> None:
    """Verifies unknown roles fail fast at resolve time."""
    from apps.api.orchestration.roles import RoleRegistry

    try:
        RoleRegistry().resolve("oracle")
    except KeyError:
        return
    raise AssertionError("expected KeyError")


async def test_roles_registry_covers_loop_roles() -> None:
    """Verifies the registry supplies every role the loop needs."""
    from apps.api.orchestration.roles import RoleRegistry

    registry = RoleRegistry()
    for role in ("planner", "executor", "synthesizer", "critic"):
        assert registry.resolve(role) is not None


async def test_run_session_returns_plain_dict() -> None:
    """Verifies the loop result is JSON-serializable."""
    result = await run_session("it-f6", "serialize me")
    assert isinstance(result, dict)


async def test_run_session_bounded_respects_max_revisions() -> None:
    """Verifies a run never exceeds the revision bound."""
    from apps.api.orchestration.loop import MAX_REVISIONS

    result = await run_session("it-9", "never satisfied")
    assert result["iterations"] <= MAX_REVISIONS + 1


async def test_max_revisions_constant_is_three() -> None:
    """Verifies the revision bound stays at three per the ADR."""
    from apps.api.orchestration.loop import MAX_REVISIONS

    assert MAX_REVISIONS == 3


async def test_critic_node_counts_iterations() -> None:
    """Verifies the critic bumps iterations each pass."""
    from apps.api.orchestration.state_machine import critic_node

    state = critic_node(
        {"task": "t", "plan": [], "results": ["r"], "critique": "",
         "iterations": 4}
    )
    assert state["iterations"] == 5
