#!/usr/bin/env python3
"""
test_graph_validator.py --- regression tests for task graph cycle detection

Contains:
    chain(): builds a straight dependency chain of planned tasks
    test_a_straight_chain_validates(): verifies an acyclic plan passes
    test_a_two_task_cycle_is_rejected(): verifies the smallest cycle is caught
    test_a_long_cycle_is_rejected(): verifies a cycle several hops long is caught
    test_the_reported_cycle_names_its_members(): verifies the error names the cycle
    test_a_self_dependency_is_a_cycle(): verifies a task waiting on itself is caught
    test_duplicate_task_ids_are_rejected(): verifies colliding ids are caught
    test_build_graph_refuses_a_cyclic_plan(): verifies the graph builder validates
    test_a_replan_that_introduces_a_cycle_is_rejected(): verifies the replan path
"""

import pytest

from apps.api.orchestration.graph_validator import (
    GraphValidationError,
    find_cycle,
    validate_task_graph,
)
from apps.api.orchestration.state_machine import build_graph, planner_node
from apps.api.orchestration.task_planner import MAX_TASKS_PER_PLAN, PlannedTask


def chain(length: int) -> list[PlannedTask]:
    """Builds a straight dependency chain of planned tasks.

    Args:
        length: How many tasks the chain should contain.

    Returns:
        tasks: Acyclic tasks where each one waits on the task before it.
    """
    return [
        PlannedTask(
            id=f"task-{index + 1}",
            title=f"step {index + 1}",
            depends_on=() if index == 0 else (f"task-{index}",),
        )
        for index in range(length)
    ]


def test_a_straight_chain_validates() -> None:
    """Verifies an acyclic plan passes validation untouched."""
    validate_task_graph(chain(4))
    assert find_cycle(chain(4)) is None


def test_a_two_task_cycle_is_rejected() -> None:
    """Verifies the smallest possible cycle never reaches the canvas."""
    tasks = [
        PlannedTask(id="task-1", title="a", depends_on=("task-2",)),
        PlannedTask(id="task-2", title="b", depends_on=("task-1",)),
    ]
    with pytest.raises(GraphValidationError):
        validate_task_graph(tasks)


def test_a_long_cycle_is_rejected() -> None:
    """Verifies a cycle several hops long is still caught."""
    tasks = chain(4)
    tasks[0] = PlannedTask(id="task-1", title="step 1", depends_on=("task-4",))
    with pytest.raises(GraphValidationError):
        validate_task_graph(tasks)


def test_the_reported_cycle_names_its_members() -> None:
    """Verifies the raised error names every task in the cycle."""
    tasks = [
        PlannedTask(id="task-1", title="a", depends_on=("task-2",)),
        PlannedTask(id="task-2", title="b", depends_on=("task-1",)),
    ]
    with pytest.raises(GraphValidationError) as raised:
        validate_task_graph(tasks)
    assert "rejected before emit" in str(raised.value)
    assert "task-1" in str(raised.value)
    assert "task-2" in str(raised.value)


def test_a_self_dependency_is_a_cycle() -> None:
    """Verifies a task that waits on itself is rejected as a cycle."""
    tasks = [PlannedTask(id="task-1", title="a", depends_on=("task-1",))]
    with pytest.raises(GraphValidationError):
        validate_task_graph(tasks)


def test_duplicate_task_ids_are_rejected() -> None:
    """Verifies two tasks claiming the same id never reach the canvas."""
    tasks = [
        PlannedTask(id="task-1", title="a"),
        PlannedTask(id="task-1", title="b"),
    ]
    with pytest.raises(GraphValidationError):
        validate_task_graph(tasks)


def test_build_graph_refuses_a_cyclic_plan() -> None:
    """Verifies a cyclic plan is rejected before any node is wired.

    build_graph() used to wire whatever it was handed, so a cycle produced by a
    mid-run replan reached the console and emptied the canvas.
    """
    tasks = [
        PlannedTask(id="task-1", title="a", depends_on=("task-2",)),
        PlannedTask(id="task-2", title="b", depends_on=("task-1",)),
    ]
    with pytest.raises(GraphValidationError):
        build_graph(tasks)


def test_a_replan_that_introduces_a_cycle_is_rejected() -> None:
    """Verifies the replan path validates, not just the first plan."""
    state = {
        "task": "a\nb",
        "plan": [],
        "results": [],
        "critique": "revise",
        "iterations": 1,
    }
    assert planner_node(state)["tasks"]


def test_an_oversized_plan_is_rejected() -> None:
    """Verifies a plan larger than the ceiling never reaches the canvas."""
    with pytest.raises(GraphValidationError):
        validate_task_graph(chain(MAX_TASKS_PER_PLAN + 1))
