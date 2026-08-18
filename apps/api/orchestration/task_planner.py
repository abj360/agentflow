#!/usr/bin/env python3
"""
task_planner.py --- runtime planner that emits a dependency-carrying task list

Contains:
    TaskWire: one planned task in the shape the console's graph model reads
    PlannedTask: one runtime-planned unit of work and what it waits on
    PlannedTask.to_wire(): renders the task in the shape the console consumes
    task_id(): builds the stable id for a task at a plan position
    split_objectives(): splits a task description into separately planned objectives
    branch_roots(): maps every task to the root its plan branch descends from
    TaskPlanner: turns a task description into a dependency-linked task list
    TaskPlanner.plan(): builds the task list for one run
"""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal, TypedDict

TaskStatus = Literal["pending", "running", "awaiting-approval", "done", "failed"]

DEFAULT_ASSIGNEE = "executor"
MAX_TASKS_PER_PLAN = 12


class TaskWire(TypedDict):
    """Represents one planned task in the shape the console's graph model reads.

    Attributes:
        id: Stable identifier the console keys its graph node on.
        title: Human-readable summary of the work this task covers.
        assignee: Role responsible for running the task.
        status: Lifecycle state the task is currently in.
        dependsOn: Ids of the tasks that must finish before this one starts.
        startedAt: Epoch seconds the task began running, null until it starts.
        finishedAt: Epoch seconds the task settled, null until it settles.
        tokens: Model tokens the task has consumed so far.
        retries: Times the task has been retried after a failure.
        toolCallCount: Governed tool calls the task has made.
    """

    id: str
    title: str
    assignee: str
    status: TaskStatus
    dependsOn: list[str]
    startedAt: float | None
    finishedAt: float | None
    tokens: int
    retries: int
    toolCallCount: int


@dataclass(frozen=True)
class PlannedTask:
    """Represents one runtime-planned unit of work and what it waits on.

    Attributes:
        id: Stable identifier the console keys its graph node on.
        title: Human-readable summary of the work this task covers.
        assignee: Role responsible for running the task.
        status: Lifecycle state the task is currently in.
        depends_on: Ids of the tasks that must finish before this one starts.
        started_at: Epoch seconds the task began running, None until it starts.
        finished_at: Epoch seconds the task settled, None until it settles.
        tokens: Model tokens the task has consumed so far.
        retries: Times the task has been retried after a failure.
        tool_call_count: Governed tool calls the task has made.
    """

    id: str
    title: str
    assignee: str = DEFAULT_ASSIGNEE
    status: TaskStatus = "pending"
    depends_on: tuple[str, ...] = ()
    started_at: float | None = None
    finished_at: float | None = None
    tokens: int = 0
    retries: int = 0
    tool_call_count: int = 0

    def to_wire(self) -> TaskWire:
        """Renders the task in the shape the console's graph model consumes.

        Returns:
            wire_task: Task fields keyed the way the canvas expects them.
        """
        return {
            "id": self.id,
            "title": self.title,
            "assignee": self.assignee,
            "status": self.status,
            "dependsOn": list(self.depends_on),
            "startedAt": self.started_at,
            "finishedAt": self.finished_at,
            "tokens": self.tokens,
            "retries": self.retries,
            "toolCallCount": self.tool_call_count,
        }


def task_id(index: int) -> str:
    """Builds the stable id for the task at a plan position.

    Args:
        index: Zero-based position of the task within the plan.

    Returns:
        identifier: Id the console keys this task's graph node on.
    """
    return f"task-{index + 1}"


def split_objectives(task: str) -> tuple[str, ...]:
    """Splits a task description into the objectives worth planning separately.

    Args:
        task: The user's task description, one objective per line when multi-line.

    Returns:
        objectives: Objective lines, or a single-entry tuple for a one-line task.
    """
    lines = tuple(
        stripped for stripped in (line.strip(" -\t") for line in task.splitlines()) if stripped
    )
    return lines


def branch_roots(tasks: Sequence[PlannedTask]) -> dict[str, str]:
    """Maps every task id to the root task its plan branch descends from.

    Args:
        tasks: Runtime-planned tasks carrying the ids they depend on.

    Returns:
        roots: Root task id per task id, so each branch is budgeted on its own.
            A task whose dependency is not in the plan is its own root.
    """
    by_id = {task.id: task for task in tasks}
    roots: dict[str, str] = {}
    for task in tasks:
        current = task
        # Callers validate first, so this bound is belt and braces rather than
        # the thing standing between a cyclic plan and the canvas.
        for _ in range(len(tasks)):
            parent = by_id.get(current.depends_on[0]) if current.depends_on else None
            if parent is None:
                break
            current = parent
        roots[task.id] = current.id
    return roots


class TaskPlanner:
    """Turns a task description into a dependency-linked list of planned tasks.

    Attributes:
        max_tasks: Ceiling on how many tasks a single plan may contain.
    """

    def __init__(self, max_tasks: int = MAX_TASKS_PER_PLAN) -> None:
        """Initializes the planner with a plan-size ceiling.

        Args:
            max_tasks: Ceiling on how many tasks a single plan may contain.
        """
        self.max_tasks = max_tasks

    def plan(self, task: str) -> tuple[PlannedTask, ...]:
        """Builds the task list for one run.

        Args:
            task: The user's task description.

        Returns:
            planned_tasks: Ordered tasks, each carrying the ids it depends on.
        """
        objectives = split_objectives(task)[: self.max_tasks]
        planned = [
            PlannedTask(
                id=task_id(index),
                title=objective,
                depends_on=(task_id(index - 1),) if index else (),
            )
            for index, objective in enumerate(objectives)
        ]
        return tuple(planned)
