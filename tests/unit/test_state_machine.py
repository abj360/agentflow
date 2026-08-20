#!/usr/bin/env python3
"""
test_state_machine.py --- unit tests for the orchestration state machine

Contains:
    test_graph_carries_orchestrator_and_critic(): verifies the fixed spine exists
    test_planner_seeds_plan_with_task(): verifies the planner puts the task in the plan
    test_task_nodes_announce_their_status_transitions(): verifies the status sink
"""

from apps.api.orchestration.state_machine import build_graph, planner_node
from apps.api.orchestration.task_planner import PlannedTask, TaskPlanner


def make_state(**overrides: object) -> dict:
    """Builds a graph state dict for tests.

    Args:
        overrides: Field overrides applied on the default state.

    Returns:
        state: Graph state dict with sensible defaults.
    """
    state = {"task": "t", "plan": [], "results": [], "critique": "", "iterations": 0}
    state.update(overrides)
    return state


def test_graph_carries_orchestrator_and_critic() -> None:
    """Verifies the orchestrator and critic spine survives a dynamic plan."""
    graph = build_graph(list(TaskPlanner().plan("a\nb")))
    assert {"orchestrator", "critic"} <= set(graph.nodes)


def test_graph_adds_one_node_per_planned_task() -> None:
    """Verifies every planned task becomes its own graph node."""
    planned = list(TaskPlanner().plan("first\nsecond\nthird"))
    graph = build_graph(planned)
    assert {task.id for task in planned} <= set(graph.nodes)


def test_planner_seeds_plan_with_task() -> None:
    """Verifies the planner puts the task in the plan."""
    assert planner_node(make_state(task="ship it"))["plan"] == ["ship it"]


def test_route_after_critic_accepts_on_verdict() -> None:
    """Verifies an accept verdict ends the run."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state(critique="accept")) == "accept"


def test_route_after_critic_revises_on_reject() -> None:
    """Verifies a non-accept verdict loops back to the planner."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state(critique="revise")) == "revise"


def test_critic_increments_iterations() -> None:
    """Verifies each critic pass bumps the iteration counter."""
    from apps.api.orchestration.state_machine import critic_node

    assert critic_node(make_state())["iterations"] == 1


def test_critic_revises_when_no_results() -> None:
    """Verifies empty executor output triggers a revision request."""
    from apps.api.orchestration.state_machine import critic_node

    assert critic_node(make_state())["critique"] == "revise"


def test_executor_produces_one_result_per_step() -> None:
    """Verifies executor output cardinality matches the plan."""
    from apps.api.orchestration.state_machine import executor_node

    assert len(executor_node(make_state(plan=["a", "b"]))["results"]) == 2


def test_executor_handles_empty_plan() -> None:
    """Verifies an empty plan yields zero results rather than an error."""
    from apps.api.orchestration.state_machine import executor_node

    assert executor_node(make_state())["results"] == []


def test_validate_graph_accepts_built_graph() -> None:
    """Verifies the assembled graph passes validation."""
    from apps.api.orchestration.state_machine import validate_graph

    assert validate_graph(build_graph(list(TaskPlanner().plan("x")))) == []


def test_validate_graph_flags_missing_nodes() -> None:
    """Verifies validation reports a graph with missing roles."""

    class EmptyGraph:
        """Minimal stand-in exposing a nodes attribute."""

        nodes: dict = {}

    from apps.api.orchestration.state_machine import validate_graph

    problems = validate_graph(EmptyGraph())
    assert "orchestrator node missing" in problems


def test_route_after_critic_handles_empty_critique() -> None:
    """Verifies an empty critique is treated as a revision request."""
    from apps.api.orchestration.state_machine import route_after_critic

    assert route_after_critic(make_state()) == "revise"


def test_executor_marks_results_with_done_prefix() -> None:
    """Verifies executor results carry the done marker per step."""
    from apps.api.orchestration.state_machine import executor_node

    results = executor_node(make_state(plan=["step"]))["results"]
    assert results == ["done: step"]


def test_critic_accepts_when_results_present() -> None:
    """Verifies the critic accepts once results exist."""
    from apps.api.orchestration.state_machine import critic_node

    assert critic_node(make_state(results=["r"]))["critique"] == "accept"


def test_task_nodes_announce_their_status_transitions() -> None:
    """Verifies each task node reports running and then done to the sink."""
    from apps.api.orchestration.state_machine import task_runner

    seen: list[tuple[str, str]] = []
    node = task_runner(
        PlannedTask(id="task-1", title="a"),
        "task-1",
        lambda task_id, status: seen.append((task_id, status)),
    )
    node(make_state())
    assert seen == [("task-1", "running"), ("task-1", "done")]


def test_task_nodes_run_without_a_status_sink() -> None:
    """Verifies a graph built with no sink still executes its task nodes."""
    from apps.api.orchestration.state_machine import task_runner

    node = task_runner(PlannedTask(id="task-1", title="a"), "task-1")
    assert node(make_state())["results"] == ["done: a"]
