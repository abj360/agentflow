#!/usr/bin/env python3
"""
task_planner.py --- runtime planner that emits a dependency-carrying task list

Contains:
    PlannedTask: one runtime-planned unit of work and what it waits on
    PlannedTask.to_wire(): renders the task in the shape the console consumes
    task_id(): builds the stable id for a task at a plan position
    split_objectives(): splits a task description into separately planned objectives
    TaskPlanner: turns a task description into a dependency-linked task list
    TaskPlanner.plan(): builds the task list for one run
"""

from dataclasses import dataclass
from typing import Literal

TaskStatus = Literal["pending", "running", "awaiting-approval", "done", "failed"]

DEFAULT_ASSIGNEE = "executor"
MAX_TASKS_PER_PLAN = 12


@dataclass(frozen=True)
class PlannedTask:
    """Represents one runtime-planned unit of work and what it waits on.

    Attributes:
        id: Stable identifier the console keys its graph node on.
        title: Human-readable summary of the work this task covers.
        assignee: Role responsible for running the task.
        status: Lifecycle state the task is currently in.
        depends_on: Ids of the tasks that must finish before this one starts.
    """

    id: str
    title: str
    assignee: str = DEFAULT_ASSIGNEE
    status: TaskStatus = "pending"
    depends_on: tuple[str, ...] = ()

    def to_wire(self) -> dict[str, object]:
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
    lines = tuple(line.strip(" -\t") for line in task.splitlines() if line.strip())
    if len(lines) > 1:
        return lines
    return lines[:1]


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
