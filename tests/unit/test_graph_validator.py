#!/usr/bin/env python3
"""
test_graph_validator.py --- regression tests for task graph cycle detection

Contains:
    chain(): builds a straight dependency chain of planned tasks
    test_a_straight_chain_validates(): verifies an acyclic plan passes
    test_a_two_task_cycle_is_rejected(): verifies the smallest cycle is caught
    test_a_long_cycle_is_rejected(): verifies a cycle several hops long is caught
    test_the_reported_cycle_names_its_members(): verifies the error names the cycle
"""

import pytest

from apps.api.orchestration.graph_validator import (
    GraphValidationError,
    find_cycle,
    validate_task_graph,
)
from apps.api.orchestration.task_planner import PlannedTask


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
    assert "task-1" in str(raised.value)
    assert "task-2" in str(raised.value)
