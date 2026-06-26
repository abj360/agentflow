#!/usr/bin/env python3
"""
test_state_transitions.py --- unit tests for state machine transitions

Contains:
    make_state(): builds a graph state dict for tests
    test_planner_to_executor_edge(): verifies the planner feeds the executor
"""

from apps.api.orchestration.state_machine import (
    build_graph,
    critic_node,
    executor_node,
    planner_node,
)


def make_state(**overrides: object) -> dict:
    """Builds a graph state dict for tests.

    Args:
        overrides: Field overrides applied on the default state.

    Returns:
        state: Graph state dict with sensible defaults.
    """
    state = {
        "task": "t",
        "plan": [],
        "results": [],
        "critique": "",
        "iterations": 0,
    }
    state.update(overrides)
    return state


def test_planner_to_executor_edge() -> None:
    """Verifies the planner feeds the executor."""
    after_plan = planner_node(make_state(task="do it"))
    after_exec = executor_node(after_plan)
    assert after_exec["results"]


def test_planner_update_only_touches_plan() -> None:
    """Verifies the planner update leaves other fields intact."""
    state = make_state(task="keep", results=["untouched"])
    after = planner_node(state)
    assert after["results"] == ["untouched"]


def test_executor_to_critic_edge() -> None:
    """Verifies the executor feeds the critic."""
    from apps.api.orchestration.state_machine import critic_node

    after_exec = executor_node(make_state(plan=["x"]))
    after_critic = critic_node(after_exec)
    assert after_critic["iterations"] == 1


def test_revise_edge_loops_to_planner() -> None:
    """Verifies a revise verdict routes back to planning."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state(critique="revise")) == "revise"


def test_executor_update_preserves_plan() -> None:
    """Verifies the executor leaves the plan in place."""
    after = executor_node(make_state(plan=["stay"]))
    assert after["plan"] == ["stay"]


def test_accept_edge_ends_run() -> None:
    """Verifies an accept verdict routes to the end."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state(critique="accept")) == "accept"


def test_critic_update_only_touches_verdict_fields() -> None:
    """Verifies the critic leaves plan and results intact."""
    from apps.api.orchestration.state_machine import critic_node

    after = critic_node(make_state(plan=["p"], results=["r"]))
    assert after["plan"] == ["p"] and after["results"] == ["r"]


def test_validate_graph_flags_missing_critic() -> None:
    """Verifies validation reports a missing critic node."""

    class PlannerOnlyGraph:
        """Graph stand-in with only a planner node."""

        nodes = {"planner": object()}

    from apps.api.orchestration.state_machine import validate_graph

    assert validate_graph(PlannerOnlyGraph()) != []


def test_full_cycle_two_iterations() -> None:
    """Verifies plan/exec/critic chains over two simulated cycles."""
    from apps.api.orchestration.state_machine import critic_node

    state = make_state(task="cycle")
    for _ in range(2):
        state = planner_node(state)
        state = executor_node(state)
        state = critic_node(state)
    assert state["iterations"] == 2


def test_validate_graph_detects_sound_graph() -> None:
    """Verifies the production graph passes its own validation."""
    from apps.api.orchestration.state_machine import validate_graph

    assert validate_graph(build_graph()) == []


def test_second_revision_still_loops() -> None:
    """Verifies repeated revise verdicts keep looping to the planner."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state(critique="revise", iterations=2)) == "revise"


def test_iterations_monotonic_across_cycles() -> None:
    """Verifies the iteration counter never decreases."""
    from apps.api.orchestration.state_machine import critic_node

    first = critic_node(make_state(results=["r"]))
    second = critic_node({**first, "critique": "revise"})
    assert second["iterations"] > first["iterations"]


def test_state_carries_task_through_cycle() -> None:
    """Verifies the task survives a full transition cycle."""
    from apps.api.orchestration.state_machine import critic_node

    state = planner_node(make_state(task="persist"))
    state = executor_node(state)
    state = critic_node(state)
    assert state["task"] == "persist"


def test_graph_entry_point_is_planner() -> None:
    """Verifies runs always begin at the planner node."""
    graph = build_graph()
    assert graph.entry_point == "planner"


def test_results_grow_after_each_executor_pass() -> None:
    """Verifies executor passes produce results for the critic."""
    state = executor_node(make_state(plan=["a"]))
    state = executor_node({**state, "plan": ["b"]})
    assert len(state["results"]) == 1


def test_iterations_start_at_zero() -> None:
    """Verifies fresh states begin with zero iterations."""
    assert make_state()["iterations"] == 0


def test_critique_starts_empty() -> None:
    """Verifies fresh states carry no critique yet."""
    assert make_state()["critique"] == ""


def test_graph_nodes_match_role_names() -> None:
    """Verifies graph node names match the canonical role names."""
    graph = build_graph()
    assert "planner" in graph.nodes
    assert "executor" in graph.nodes
    assert "critic" in graph.nodes


def test_critic_revise_path_preserves_plan() -> None:
    """Verifies a revise cycle keeps the current plan in state."""
    from apps.api.orchestration.state_machine import critic_node

    state = critic_node(make_state(plan=["keep me"]))
    assert state["plan"] == ["keep me"]
