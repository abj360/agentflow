#!/usr/bin/env python3
"""
graph_validator.py --- rejects an unsound task graph before it reaches the canvas

Contains:
    GraphValidationError: raised when a task list cannot be rendered as a DAG
    find_unknown_assignees(): returns assignees no role in the registry answers to
    find_duplicate_ids(): returns task ids the plan declares more than once
    find_dangling_dependencies(): returns dependsOn ids naming no task in the plan
    find_cycle(): returns the first dependency cycle found in a task list
    validate_task_graph(): raises when a task list is not a renderable DAG,
        is larger than one plan may be, or names a task it never declares
"""

from collections.abc import Sequence

from apps.api.orchestration.roles import RoleRegistry
from apps.api.orchestration.task_planner import MAX_TASKS_PER_PLAN, PlannedTask


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
        super().__init__("task graph rejected before emit: " + "; ".join(problems))


def find_unknown_assignees(tasks: Sequence[PlannedTask]) -> tuple[str, ...]:
    """Returns the assignees that no registered role answers to.

    A task assigned to a role that does not exist fails at execution time, long
    after the console has drawn it. Catching it here keeps the canvas honest.

    Args:
        tasks: Planned tasks carrying the role each one is assigned to.

    Returns:
        unknown: Assignee names with no matching role, in first-seen order.
    """
    known = set(RoleRegistry().roles)
    unknown: list[str] = []
    for task in tasks:
        if task.assignee not in known and task.assignee not in unknown:
            unknown.append(task.assignee)
    return tuple(unknown)


def find_duplicate_ids(tasks: Sequence[PlannedTask]) -> tuple[str, ...]:
    """Returns the task ids the plan declares more than once.

    Args:
        tasks: Planned tasks to check for id collisions.

    Returns:
        duplicates: Ids seen more than once, in first-seen order.
    """
    seen: set[str] = set()
    duplicates: list[str] = []
    for task in tasks:
        if task.id in seen and task.id not in duplicates:
            duplicates.append(task.id)
        seen.add(task.id)
    return tuple(duplicates)


def find_dangling_dependencies(tasks: Sequence[PlannedTask]) -> tuple[str, ...]:
    """Returns the dependsOn ids that name no task in the plan.

    Args:
        tasks: Planned tasks carrying the ids they depend on.

    Returns:
        dangling: Referenced ids the plan never declares, in first-seen order.
    """
    planned = {task.id for task in tasks}
    dangling: list[str] = []
    for task in tasks:
        for dependency in task.depends_on:
            if dependency not in planned and dependency not in dangling:
                dangling.append(dependency)
    return tuple(dangling)


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
    if not tasks:
        return
    problems = [
        *([f"plan exceeds {MAX_TASKS_PER_PLAN} tasks"] if len(tasks) > MAX_TASKS_PER_PLAN else []),
        *(f"duplicate task id: {duplicate}" for duplicate in find_duplicate_ids(tasks)),
        *(
            f"dependsOn names a task the plan never declares: {dangling}"
            for dangling in find_dangling_dependencies(tasks)
        ),
    ]
    cycle = find_cycle(tasks)
    if cycle is not None:
        problems.append("dependsOn cycle: " + " -> ".join(cycle))
    if problems:
        raise GraphValidationError(problems)
