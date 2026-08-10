#!/usr/bin/env python3
"""
graph_validator.py --- rejects an unsound task graph before it reaches the canvas

Contains:
    GraphValidationError: raised when a task list cannot be rendered as a DAG
    find_cycle(): returns the first dependency cycle found in a task list
    validate_task_graph(): raises when a task list is not a renderable DAG
"""

from collections.abc import Sequence

from apps.api.orchestration.task_planner import PlannedTask


class GraphValidationError(ValueError):
    """Raised when a planned task list cannot be rendered as a DAG.

    Attributes:
        problems: Human-readable description of every problem found.
    """

    def __init__(self, problems: Sequence[str]) -> None:
        """Initializes the error with the problems that blocked validation.

        Args:
            problems: Human-readable description of every problem found.
        """
        self.problems = tuple(problems)
        super().__init__("; ".join(problems))


def find_cycle(tasks: Sequence[PlannedTask]) -> tuple[str, ...] | None:
    """Returns the first dependency cycle found in a task list.

    Args:
        tasks: Planned tasks carrying the ids they depend on.

    Returns:
        cycle: Task ids forming the cycle, or None when the graph is acyclic.
    """
    dependencies = {task.id: tuple(task.depends_on) for task in tasks}
    visiting: list[str] = []
    settled: set[str] = set()

    def walk(node: str) -> tuple[str, ...] | None:
        """Walks one dependency chain looking for a node it is already inside.

        Args:
            node: Task id to descend from.

        Returns:
            cycle: Ids forming the cycle, or None when this chain is acyclic.
        """
        if node in settled:
            return None
        if node in visiting:
            return (*visiting[visiting.index(node) :], node)
        visiting.append(node)
        for dependency in dependencies.get(node, ()):
            cycle = walk(dependency)
            if cycle is not None:
                return cycle
        visiting.pop()
        settled.add(node)
        return None

    for task in tasks:
        cycle = walk(task.id)
        if cycle is not None:
            return cycle
    return None


def validate_task_graph(tasks: Sequence[PlannedTask]) -> None:
    """Raises when a planned task list is not a graph the canvas can render.

    Args:
        tasks: Planned tasks to check before any structural event is emitted.
    """
    cycle = find_cycle(tasks)
    if cycle is not None:
        raise GraphValidationError(["dependency cycle: " + " -> ".join(cycle)])
